from rest_framework import serializers

from api.models.asset import Asset
from api.serializers.user import UserSerializer


class AssetSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Asset
        fields = [
            "id",
            "title",
            "description",
            "filter",
            "created_at",
            "updated_at",
            "created_by",
        ]
        extra_kwargs = {"filter": {"default": ""}}

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["project"] = request.project
        validated_data["created_by"] = request.user
        return super().create(validated_data)
