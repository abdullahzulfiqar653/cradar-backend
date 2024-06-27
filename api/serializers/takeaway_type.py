from rest_framework import serializers

from api.models.takeaway_type import TakeawayType


class TakeawayTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TakeawayType
        fields = ["id", "name", "project", "definition"]

    def validate_name(self, name):
        # Validation during creation
        request = self.context["request"]
        if (
            hasattr(request, "project")
            and request.project.takeaway_types.filter(name=name).exists()
        ):
            raise serializers.ValidationError(
                "Takeaway type with this name already exists in this project."
            )

        # Validation during update
        if (
            self.instance
            and self.instance.name != name
            and self.instance.project.takeaway_types.filter(name=name).exists()
        ):
            raise serializers.ValidationError(
                "Takeaway type with this name already exists in this project."
            )

        return name

    def create(self, validated_data):
        validated_data["project"] = self.context["request"].project
        return super().create(validated_data)
