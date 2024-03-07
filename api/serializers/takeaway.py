from rest_framework import exceptions, serializers

from api.models.block import Block
from api.models.insight import Insight
from api.models.note import Note
from api.models.takeaway import Takeaway
from api.models.takeaway_type import TakeawayType
from api.serializers.question import QuestionSerializer
from api.serializers.tag import TagSerializer
from api.serializers.user import UserSerializer


class BriefNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = [
            "id",
            "title",
        ]


class TakeawaySerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    type = serializers.CharField(source="type.name", required=False, allow_null=True)
    report = BriefNoteSerializer(source="note", read_only=True)
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = Takeaway
        fields = [
            "id",
            "title",
            "tags",
            "type",
            "description",
            "priority",
            "created_by",
            "report",
            "created_at",
            "question",
        ]

    def create(self, validated_data):
        request = self.context["request"]
        takeaway_type_data = validated_data.pop("type", None)
        if takeaway_type_data is not None and takeaway_type_data["name"] is not None:
            takeaway_type, _ = TakeawayType.objects.get_or_create(
                name=takeaway_type_data["name"], project=request.note.project
            )
            validated_data["type"] = takeaway_type

        validated_data["created_by"] = request.user
        validated_data["note"] = request.note
        return super().create(validated_data)

    def update(self, takeaway, validated_data):
        if "type" in validated_data:
            takeaway_type_data = validated_data.pop("type")
            if takeaway_type_data["name"]:
                takeaway_type, _ = TakeawayType.objects.get_or_create(
                    name=takeaway_type_data["name"], project=takeaway.note.project
                )
                takeaway.type = takeaway_type
            else:
                # User remove takeaway type
                takeaway.type = None
        return super().update(takeaway, validated_data)


class TakeawayIDsSerializer(serializers.Serializer):
    id = serializers.CharField()

    def validate_id(self, value):
        if value not in self.context["valid_takeaway_ids"]:
            raise exceptions.ValidationError(
                f"Takeaway {value} not in the insight project."
            )
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
        # Only remove takeaways that are in insight
        takeaways_to_remove = block.takeaways.filter(id__in=takeaway_ids)
        block.takeaways.remove(*takeaways_to_remove)
        self.instance = {"takeaways": takeaways_to_remove}
