from ordered_model.serializers import OrderedModelSerializer
from rest_framework import serializers

from api.models.block import Block


class BlockSerializer(OrderedModelSerializer, serializers.ModelSerializer):
    order = serializers.IntegerField(required=False)

    class Meta:
        model = Block
        fields = [
            "id",
            "type",
            "order",
            "question",
            "content",
            "filter",
        ]
        read_only_fields = ["question", "filter"]

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["asset"] = request.asset
        return super().create(validated_data)


class BlockGenerateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = [
            "question",
            "content",
            "filter",
        ]
        extra_kwargs = {
            "question": {"allow_blank": False, "required": True},
            "content": {"read_only": True},
            "filter": {
                "help_text": "The url query string to filter takeaways.",
                "default": None,
            },
        }
