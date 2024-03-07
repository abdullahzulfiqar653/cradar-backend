from rest_framework import serializers

from api.models.insight import Insight
from api.serializers.user import UserSerializer


class ProjectInsightSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    created_by = UserSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    takeaway_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Insight
        fields = [
            "id",
            "title",
            "created_at",
            "created_by",
            "takeaway_count",
        ]

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["project"] = request.project
        validated_data["created_by"] = request.user
        return super().create(validated_data)


class InsightSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Insight
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "created_by",
        ]
