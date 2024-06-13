from rest_framework import serializers

from api.models.tag import Tag
from api.models.keyword import Keyword


class TagSerializer(serializers.ModelSerializer):
    takeaway_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = ["id", "name", "color", "project",  "takeaway_count"]
        validators = []  # To skip unique together constraint

    def get_project(self):
        """
        Helper method to retrieve the project from the context.
        """
        request = self.context.get('request')
        if hasattr(request, 'tag_board'):
            return request.tag_board.project
        if hasattr(request, 'takeaway'):
            return request.takeaway.note.project
        raise serializers.ValidationError("Project information is missing in the request context.")
    
    def validate_name(self, value):
        if hasattr(self.context.get("request"), 'tag_board'):
            tag_board = self.context.get("request").tag_board
            if tag_board.tags.filter(name=value).exists():
                raise serializers.ValidationError(
                        f"'{value}' tag already exists for this tag board."
                    )
        return value

    def create(self, validated_data):
        validated_data['project'] = self.get_project()
        if hasattr(self.context.get("request"), 'tag_board'):
            validated_data['tag_board'] = self.context.get("request").tag_board
            return super().create(validated_data)
        if hasattr(self.context.get("request"), 'takeaway'):
            tag = Tag.objects.create(**validated_data)
            self.context.get("request").takeaway.tags.add(tag)
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
