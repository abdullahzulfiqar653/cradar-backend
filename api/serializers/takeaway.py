from django.db import models
from rest_framework import exceptions, serializers

from api.ai.embedder import embedder
from api.models.block import Block
from api.models.insight import Insight
from api.models.note import Note
from api.models.takeaway import Takeaway
from api.models.takeaway_type import TakeawayType
from api.models.theme import Theme
from api.models.user import User
from api.serializers.organization import OrganizationSerializer
from api.serializers.tag import TagSerializer
from api.serializers.takeaway_type import TakeawayTypeSerializer
from api.serializers.user import UserSerializer


class BriefNoteSerializer(serializers.ModelSerializer):
    organizations = OrganizationSerializer(read_only=True, many=True)

    class Meta:
        model = Note
        fields = [
            "id",
            "title",
            "organizations",
        ]


class TakeawaySerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    type = TakeawayTypeSerializer(read_only=True)
    type_id = serializers.PrimaryKeyRelatedField(
        source="type",
        queryset=TakeawayType.objects.none(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    report = BriefNoteSerializer(source="note", read_only=True)
    is_saved = serializers.BooleanField(read_only=True)
    quote = serializers.CharField(source="highlight.quote", read_only=True)

    class Meta:
        model = Takeaway
        fields = [
            "id",
            "title",
            "tags",
            "type",
            "type_id",
            "description",
            "priority",
            "created_by",
            "report",
            "created_at",
            "is_saved",
            "quote",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if hasattr(request, "note"):
            self.fields["type_id"].queryset = request.note.project.takeaway_types.all()
        elif hasattr(request, "takeaway"):
            self.fields["type_id"].queryset = (
                request.takeaway.note.project.takeaway_types.all()
            )

    @classmethod
    def optimize_query(cls, queryset, user):
        return (
            queryset.select_related("created_by", "type", "note", "highlight")
            # The following line speed up the query but gives wrong takeaway count
            # .prefetch_related("tags")
            .prefetch_related("note__organizations")
            .annotate(
                is_saved=models.Case(
                    models.When(saved_by=user, then=models.Value(True)),
                    default=models.Value(False),
                    output_field=models.BooleanField(),
                )
            )
            .only(
                "id",
                "title",
                "type",
                "description",
                "priority",
                "created_by__email",
                "created_by__first_name",
                "created_by__last_name",
                "note__id",
                "note__title",
                "created_at",
            )
        )

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["created_by"] = request.user
        validated_data["note"] = request.note
        validated_data["vector"] = embedder.embed_documents([validated_data["title"]])[
            0
        ]
        return super().create(validated_data)

    def update(self, takeaway, validated_data):
        if "title" in validated_data:
            validated_data["vector"] = embedder.embed_documents(
                [validated_data["title"]]
            )[0]
        return super().update(takeaway, validated_data)


class TakeawayIDsSerializer(serializers.Serializer):
    id = serializers.CharField()

    def validate_id(self, value):
        if value not in self.context["valid_takeaway_ids"]:
            raise exceptions.ValidationError(f"Takeaway {value} not in the project.")
        return value


class InsightTakeawaysSerializer(serializers.Serializer):
    takeaways = TakeawayIDsSerializer(many=True)

    def create(self, validated_data):
        insight: Insight = self.context["insight"]
        takeaway_ids = {takeaway["id"] for takeaway in validated_data["takeaways"]}
        # Skip adding takeaways that are already in insight
        takeaways_to_add = Takeaway.objects.filter(id__in=takeaway_ids).exclude(
            insights=insight
        )
        insight.takeaways.add(*takeaways_to_add)
        return {"takeaways": takeaways_to_add}

    def delete(self):
        insight: Insight = self.context["insight"]
        takeaway_ids = {takeaway["id"] for takeaway in self.validated_data["takeaways"]}
        # Only remove takeaways that are in insight
        takeaways_to_remove = insight.takeaways.filter(id__in=takeaway_ids)
        insight.takeaways.remove(*takeaways_to_remove)
        self.instance = {"takeaways": takeaways_to_remove}


class BlockTakeawaysSerializer(serializers.Serializer):
    takeaways = TakeawayIDsSerializer(many=True)

    def validate(self, data):
        block = self.context["block"]
        if block.type != Block.Type.TAKEAWAYS:
            raise exceptions.ValidationError(
                "Can only add takeaways to block of type 'Takeaways'. "
                f"The current block is of type '{block.type}'."
            )
        return data

    def create(self, validated_data):
        block: Block = self.context["block"]
        takeaway_ids = {takeaway["id"] for takeaway in validated_data["takeaways"]}
        # Skip adding takeaways that are already in the block
        takeaways_to_add = Takeaway.objects.filter(id__in=takeaway_ids).exclude(
            blocks=block
        )
        block.takeaways.add(*takeaways_to_add)
        return {"takeaways": takeaways_to_add}

    def delete(self):
        block: Block = self.context["block"]
        takeaway_ids = {takeaway["id"] for takeaway in self.validated_data["takeaways"]}
        # Only remove takeaways that are in the block
        takeaways_to_remove = block.takeaways.filter(id__in=takeaway_ids)
        block.takeaways.remove(*takeaways_to_remove)
        self.instance = {"takeaways": takeaways_to_remove}


class ThemeTakeawaysSerializer(serializers.Serializer):
    takeaways = TakeawayIDsSerializer(many=True)

    def create(self, validated_data):
        theme: Theme = self.context["theme"]
        takeaway_ids = {takeaway["id"] for takeaway in validated_data["takeaways"]}
        # Skip adding takeaways that are already in the theme
        takeaways_to_add = Takeaway.objects.filter(id__in=takeaway_ids).exclude(
            themes=theme
        )
        theme.takeaways.add(*takeaways_to_add)
        return {"takeaways": takeaways_to_add}

    def delete(self):
        theme: Theme = self.context["theme"]
        takeaway_ids = {takeaway["id"] for takeaway in self.validated_data["takeaways"]}
        # Only remove takeaways that are in the theme
        takeaways_to_remove = theme.takeaways.filter(id__in=takeaway_ids)
        theme.takeaways.remove(*takeaways_to_remove)
        self.instance = {"takeaways": takeaways_to_remove}


class SavedTakeawaysSerializer(serializers.Serializer):
    takeaways = TakeawayIDsSerializer(many=True)

    def create(self, validated_data):
        user: User = self.context["user"]
        takeaway_ids = {takeaway["id"] for takeaway in validated_data["takeaways"]}
        # Skip adding takeaways that are already saved by user
        takeaways_to_add = Takeaway.objects.filter(id__in=takeaway_ids).exclude(
            saved_by=user
        )
        user.saved_takeaways.add(*takeaways_to_add)
        return {"takeaways": takeaways_to_add}

    def delete(self):
        user: User = self.context["user"]
        takeaway_ids = {takeaway["id"] for takeaway in self.validated_data["takeaways"]}
        # Only remove takeaways that are in insight
        takeaways_to_remove = user.saved_takeaways.filter(id__in=takeaway_ids)
        user.saved_takeaways.remove(*takeaways_to_remove)
        self.instance = {"takeaways": takeaways_to_remove}
