# note/serializers.py
from django.db.models import Count
from rest_framework import serializers

from note.models import Note
from note.models.organization import Organization
from note.serializers.organization import OrganizationSerializer
from tag.serializers import KeywordSerializer
from takeaway.models import Highlight
from takeaway.serializers import HighlightSerializer
from user.serializers import AuthUserSerializer


class SkipIdValidatorHighlightSerializer(HighlightSerializer):
    id = serializers.CharField(read_only=False)

    class Meta:
        model = Highlight
        fields = [
            "id",
            "start",
            "end",
        ]
        extra_kwargs = {
            "id": {
                "validators": [],
            },
        }


class NoteSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    title = serializers.CharField(required=False, default="New Report")
    type = serializers.CharField(required=False, default="User Interview")
    description = serializers.CharField(required=False, default="")
    code = serializers.CharField(read_only=True)
    takeaway_count = serializers.IntegerField(read_only=True)
    participant_count = serializers.IntegerField(read_only=True)
    author = AuthUserSerializer(read_only=True)
    is_analyzing = serializers.BooleanField(read_only=True)
    is_auto_tagged = serializers.BooleanField(read_only=True)
    file_type = serializers.CharField(read_only=True)
    keywords = KeywordSerializer(many=True, required=False)
    content = serializers.CharField(required=False, default="", allow_blank=True)
    summary = serializers.CharField(required=False, default="", allow_blank=True)
    highlights = SkipIdValidatorHighlightSerializer(many=True, required=False)
    organizations = OrganizationSerializer(many=True)

    class Meta:
        model = Note
        fields = [
            "id",
            "code",
            "takeaway_count",
            "participant_count",
            "author",
            "is_analyzing",
            "is_auto_tagged",
            "file_type",
            "keywords",
            "summary",
            "title",
            "created_at",
            "organizations",
            "content",
            "revenue",
            "description",
            "type",
            "is_published",
            "file",
            "sentiment",
            "highlights",
        ]

    def validate_highlights(self, highlights):
        note_id = self.context["view"].kwargs["pk"]
        highlight_ids = {
            highlight["id"]
            for highlight in highlights
            if "id" in highlight and highlight["id"]
        }
        db_highlights = Highlight.objects.filter(note_id=note_id)
        db_highlight_ids = {highlight.id for highlight in db_highlights}
        extra = highlight_ids - db_highlight_ids
        if extra:
            raise serializers.ValidationError(
                "The highlight ids provided must match the existing highlight ids. "
                f"Provided list contains the following extra highlight ids: {extra}. "
            )

        self.db_highlights = db_highlights
        return highlights

    def create(self, validated_data):
        project_id = self.context["view"].kwargs["project_id"]
        organizations = validated_data.pop("organizations", None)
        note = Note.objects.create(**validated_data)

        for organization_dict in organizations:
            organization_name = organization_dict["name"]
            organization, _ = Organization.objects.get_or_create(
                name=organization_name, project_id=project_id
            )
            note.organizations.add(organization)

        return note

    def update(self, instance, validated_data):
        project = instance.project
        highlights = validated_data.pop("highlights", None)
        organizations = validated_data.pop("organizations", None)
        instance: Note = super().update(instance, validated_data)

        if highlights is not None:
            get_highlight = {
                highlight["id"]: highlight
                for highlight in highlights
                if "id" in highlight and highlight["id"]
            }
            for db_highlight in self.db_highlights:
                highlight = get_highlight.get(db_highlight.id)
                if highlight is None:
                    db_highlight.delete()
                else:
                    db_highlight.start = highlight["start"]
                    db_highlight.end = highlight["end"]
                    db_highlight.save()

        if organizations is not None:
            organizations_to_add = []
            for organization_dict in organizations:
                organization_name = organization_dict["name"]
                organization, _ = Organization.objects.get_or_create(
                    name=organization_name, project=project
                )
                organizations_to_add.append(organization)
            instance.organizations.set(organizations_to_add)
            # Clean up
            (
                Organization.objects.filter(project=project)
                .annotate(note_count=Count("notes"))
                .filter(note_count=0)
                .delete()
            )

        return instance


class ProjectNoteSerializer(NoteSerializer):
    content = None
    highlights = None

    class Meta(NoteSerializer.Meta):
        fields = list(set(NoteSerializer.Meta.fields) - {"content", "highlights"})


class NameOnlySerializer(serializers.Serializer):
    name = serializers.CharField()
