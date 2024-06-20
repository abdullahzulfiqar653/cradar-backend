from rest_framework import serializers

from api.models.block import Block
from api.serializers.theme import ThemeSerializer


class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = [
            "id",
            "type",
        ]
        read_only_fields = ["type"]


class BlockThemeSerializer(serializers.ModelSerializer):
    themes = ThemeSerializer(many=True, read_only=True)

    class Meta:
        model = Block
        fields = [
            "filter",
            "themes",
        ]
        extra_kwargs = {
            "filter": {
                "help_text": "The url query string to filter takeaways.",
                "default": None,
            },
        }
