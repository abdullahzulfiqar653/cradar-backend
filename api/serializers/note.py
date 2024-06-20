# note/serializers.py
import logging

import requests
from django.core.files.base import ContentFile
from django.db.models import Count
from rest_framework import exceptions, serializers

from api.ai.embedder import embedder
from api.models.highlight import Highlight
from api.models.integrations.googledrive.googledrive_user import GoogleDriveUser
from api.models.keyword import Keyword
from api.models.note import Note
from api.models.note_type import NoteType
from api.models.organization import Organization
from api.models.question import Question
from api.serializers.note_type import NoteTypeSerializer
from api.serializers.organization import OrganizationSerializer
from api.serializers.question import QuestionSerializer
from api.serializers.tag import KeywordSerializer
from api.serializers.user import UserSerializer
from api.utils.lexical import LexicalProcessor

logger = logging.getLogger(__name__)


class NoteSerializer(serializers.ModelSerializer):
    file_name = serializers.CharField(read_only=True, source="file.name")
    takeaway_count = serializers.IntegerField(read_only=True)
    author = UserSerializer(read_only=True)
    keywords = KeywordSerializer(many=True, required=False)
    questions = QuestionSerializer(many=True, required=False)
    summary = serializers.JSONField(required=False, default=[])
    organizations = OrganizationSerializer(many=True, required=False)
    google_drive_file_id = serializers.CharField(write_only=True, required=False)
    type = NoteTypeSerializer(read_only=True)
    type_id = serializers.PrimaryKeyRelatedField(
        source="type",
        queryset=NoteType.objects.none(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Note
        fields = [
            "id",
            "code",
            "takeaway_count",
            "author",
            "is_analyzing",
            "is_auto_tagged",
            "keywords",
            "questions",
            "summary",
            "title",
            "created_at",
            "organizations",
            "content",
            "revenue",
            "description",
            "type",
            "type_id",
            "is_published",
            "file",
            "file_type",
            "file_name",
            "url",
            "sentiment",
            "google_drive_file_id",
        ]
        read_only_fields = [
            "id",
            "code",
            "author",
            "is_analyzing",
            "is_auto_tagged",
            "file_type",
        ]
        extra_kwargs = {
            "title": {
                "required": False,
                "default": "New Source",
            },
            "type": {
                "required": False,
                "default": "Unassigned",
            },
            "description": {
                "required": False,
                "default": "",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if hasattr(request, "project"):
            self.fields["type_id"].queryset = request.project.note_types.all()
        elif hasattr(request, "note"):
            self.fields["type_id"].queryset = request.note.project.note_types.all()

    def validate_content(self, content):
        text = LexicalProcessor(content["root"]).to_markdown()
        if len(text) > 250_000:
            raise exceptions.ValidationError("Content exceed length limit.")
        return content

    def validate_questions(self, value):
        if len(value) > 8:
            raise exceptions.ValidationError("Please provide at most 8 questions.")
        return value

    def add_organizations(self, note, organizations):
        organizations_to_create = [
            Organization(name=organization["name"], project=note.project)
            for organization in organizations
        ]
        Organization.objects.bulk_create(organizations_to_create, ignore_conflicts=True)
        organizations_to_add = Organization.objects.filter(project=note.project).filter(
            name__in=[organization["name"] for organization in organizations]
        )
        note.organizations.add(*organizations_to_add)

    def add_keywords(self, note, keywords):
        keywords_to_create = [Keyword(name=keyword["name"]) for keyword in keywords]
        Keyword.objects.bulk_create(keywords_to_create, ignore_conflicts=True)
        keywords_to_add = Keyword.objects.filter(
            name__in=[keyword["name"] for keyword in keywords]
        )
        note.keywords.add(*keywords_to_add)

    def add_questions(self, note, questions):
        questions_to_create = [
            Question(title=question["title"], project=note.project)
            for question in questions
        ]
        Question.objects.bulk_create(questions_to_create, ignore_conflicts=True)
        questions_to_add = Question.objects.filter(project=note.project).filter(
            title__in=[question["title"] for question in questions]
        )
        note.questions.add(*questions_to_add)

    def create(self, validated_data):
        google_drive_file_id = validated_data.pop("google_drive_file_id", [])

        if google_drive_file_id:
            user = self.context["request"].user
            try:
                gdrive_user = GoogleDriveUser.objects.get(user=user)
            except GoogleDriveUser.DoesNotExist:
                raise serializers.ValidationError("Google Drive account not connected")

            headers = {"Authorization": f"Bearer {gdrive_user.access_token}"}

            file_metadata_response = requests.get(
                f"https://www.googleapis.com/drive/v3/files/{google_drive_file_id}",
                headers=headers,
            )
            file_metadata_response.raise_for_status()
            file_metadata = file_metadata_response.json()

            file_content_response = requests.get(
                f"https://www.googleapis.com/drive/v3/files/{google_drive_file_id}?alt=media",
                headers=headers,
            )
            file_content_response.raise_for_status()
            file_content = file_content_response.content

            validated_data["title"] = file_metadata.get("name")
            validated_data["file"] = ContentFile(
                file_content, name=file_metadata.get("name")
            )
            validated_data["file_type"] = file_metadata.get("mimeType")
            validated_data["file_size"] = file_metadata.get("size")
        organizations = validated_data.pop("organizations", [])
        keywords = validated_data.pop("keywords", [])
        questions = validated_data.pop("questions", [])
        note = Note.objects.create(**validated_data)
        self.add_organizations(note, organizations)
        self.add_keywords(note, keywords)
        self.add_questions(note, questions)
        return note


class NoteUpdateSerializer(NoteSerializer):
    """
    Do not allow users to update keywords and questions through note endpoint directly.
    They should use the dedicated endpoints to update keywords and questions instead.
    """

    keywords = None
    questions = None

    class Meta(NoteSerializer.Meta):
        fields = list(set(NoteSerializer.Meta.fields) - {"keywords", "questions"})

    def update(self, note: Note, validated_data):
        if note.is_analyzing:
            raise exceptions.ValidationError("Cannot update an analyzing note.")
        project = note.project
        organizations = validated_data.pop("organizations", None)
        note = super().update(note, validated_data)

        note = self.extract_highlights_from_content_state(note)

        if organizations is not None:
            organizations_to_add = []
            for organization_dict in organizations:
                organization_name = organization_dict["name"]
                organization, _ = Organization.objects.get_or_create(
                    name=organization_name, project=project
                )
                organizations_to_add.append(organization)
            note.organizations.set(organizations_to_add)
            # Clean up
            (
                Organization.objects.filter(project=project)
                .annotate(note_count=Count("notes"))
                .filter(note_count=0)
                .delete()
            )

        return note

    def extract_input_highlights(self, root: LexicalProcessor, new_highlight_id: str):
        input_highlights = {}
        for node in root.find_all("mark"):
            if None in node.dict["ids"]:
                # Replace None with the new highlight id
                # and keep the other non-None ids.
                node.dict["ids"] = [
                    id if id is not None else new_highlight_id
                    for id in node.dict["ids"]
                ]
            for id in node.dict["ids"]:
                input_highlights.setdefault(id, "")
                input_highlights[id] += node.to_text()
        return input_highlights

    def extract_highlights_from_content_state(self, note):
        # Extract highlights from rich text and update
        request = self.context["request"]
        new_highlight_id = Highlight.id.field._generate_uuid()
        root = LexicalProcessor(note.content["root"])
        input_highlights = self.extract_input_highlights(root, new_highlight_id)
        if new_highlight_id in input_highlights:
            new_highlight_text = input_highlights.get(new_highlight_id)
            Highlight.objects.create(
                id=new_highlight_id,
                title=new_highlight_text,
                quote=new_highlight_text,
                vector=embedder.embed_documents([new_highlight_text])[0],
                note=note,
                created_by=request.user,
            )

        db_highlights = {
            highlight.id: highlight for highlight in Highlight.objects.filter(note=note)
        }
        highlights_to_update = []
        for highlight_id, highlight_title in input_highlights.items():
            highlight = db_highlights.get(highlight_id)
            if highlight is None:
                # The highlight id in the note.content doesn't match with
                # any of the highlights in the db. Will skip it.
                print(highlight_id)
                logger.warn(f"The highlight {highlight_id} is not found and skipped.")
                continue
            if highlight.quote == highlight_title:
                # No need to update the highlight if the title is the same.
                continue
            highlight.quote = highlight_title
            highlight.vector = embedder.embed_documents([highlight_title])[0]
            highlights_to_update.append(highlight)
        Highlight.objects.bulk_update(highlights_to_update, ["quote", "vector"])
        note.highlights.exclude(id__in=input_highlights.keys()).delete()
        # We save the note again as we have added the highlight id
        # to the newly created highlight in the content state.
        note.save()
        return note


class ProjectNoteSerializer(NoteSerializer):
    content = None
    highlights = None

    class Meta(NoteSerializer.Meta):
        fields = list(set(NoteSerializer.Meta.fields) - {"content", "highlights"})


class ProjectSentimentSerializer(serializers.Serializer):
    name = serializers.ChoiceField(choices=Note.Sentiment.choices)
    report_count = serializers.IntegerField()
