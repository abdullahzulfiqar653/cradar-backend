from rest_framework import serializers
from api.models.tag_board import TagBoard
from api.serializers.tag import TagSerializer


class TagBoardSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = TagBoard
        exclude = ('project', )

    def get_project(self):
        """
        Helper method to retrieve the project from the context.
        """
        request = self.context.get('request')
        if hasattr(request, 'project'):
            return request.project
        if hasattr(request, 'tag_board') and hasattr(request.tag_board, 'project'):
            return request.tag_board.project
        raise serializers.ValidationError("Project information is missing in the request context.")

    def validate_name(self, value):
        project = self.get_project()
        if project.tag_boards.filter(name=value).exists():
            raise serializers.ValidationError(
                    f"'{value}' tag-board already exists for this project."
                )
        return value

    def create(self, validated_data):
        validated_data["project"] = self.get_project()
        return super().create(validated_data)
