from rest_framework import serializers

from api.models.keyword import Keyword
from api.models.tag import Tag


class TagSerializer(serializers.ModelSerializer):
    takeaway_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = ["id", "name", "color", "project",  "takeaway_count"]
        validators = []  # To skip unique together constraint
    
    def validate_name(self, value):
        tag_board = self.context.get("request").tag_board
        if tag_board.tags.filter(name=value).exists():
            raise serializers.ValidationError(
                    f"'{value}' tag already exists for this tag board."
                )
        return value

    def create(self, validated_data):
        tag_board = self.context.get("request").tag_board
        validated_data['project'] = tag_board.project
        tag = Tag.objects.create(**validated_data)
        tag.tag_board.set([tag_board])
        return tag


class KeywordSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(
        max_length=50, validators=[]  # Remove the unique validator
    )
    report_count = serializers.IntegerField(default=None, read_only=True)

    class Meta:
        model = Keyword
        fields = ["id", "name", "report_count"]

    def create(self, validated_data):
        instance, _ = Keyword.objects.get_or_create(**validated_data)
        return instance
