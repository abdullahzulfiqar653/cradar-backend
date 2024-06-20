from rest_framework import serializers

from api.ai.embedder import embedder
from api.models.note_type import NoteType


class NoteTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteType
        fields = ["id", "name", "project"]

    def validate_name(self, name):
        if (
            self.instance
            and self.instance.name != name
            and self.instance.project.note_types.filter(name=name).exists()
        ):
            raise serializers.ValidationError(
                "Report type with this name already exists in this project."
            )
        return name

    def update(self, instance, validated_data):
        if "name" in validated_data:
            validated_data["vector"] = embedder.embed_documents(
                [validated_data["name"]]
            )[0]
        return super().update(instance, validated_data)


class ProjectNoteTypeSerializer(serializers.ModelSerializer):
    report_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = NoteType
        fields = ["id", "name", "project", "report_count"]
        read_only_fields = ["project", "report_count"]

    def validate_name(self, name):
        project = self.context["request"].project
        if project.note_types.filter(name=name).exists():
            raise serializers.ValidationError(
                "Report type with this name already exists in this project."
            )
        return name

    def create(self, validated_data):
        validated_data["project"] = self.context["request"].project
        validated_data["vector"] = embedder.embed_documents([validated_data["name"]])[0]
        return super().create(validated_data)
