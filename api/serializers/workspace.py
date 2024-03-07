# workspace/serializers.py
from django.db.models import Q
from django.utils.text import slugify
from rest_framework import serializers

from api.models.workspace import Workspace


class WorkspaceSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=100)

    class Meta:
        model = Workspace
        fields = ["id", "name"]

    def validate_name(self, value):
        name = value
        slug = slugify(name)
        condition = Q(name__iexact=name) | Q(domain_slug=slug)
        if name and Workspace.objects.filter(condition).exists():
            raise serializers.ValidationError(f"Workspace Name already taken.")
        return value

    def create(self, validated_data):
        request = self.context["request"]
        workspace = Workspace(name=validated_data.get("name"), owned_by=request.user)
        workspace.save()

        request = self.context["request"]
        request.user.workspaces.add(workspace)

        return workspace


class WorkspaceDetailSerializer(WorkspaceSerializer):
    usage_minutes = serializers.SerializerMethodField()

    def get_usage_minutes(self, workspace):
        return round(workspace.usage_seconds / 60)

    class Meta:
        model = Workspace
        fields = ["id", "name", "usage_minutes", "usage_tokens", "total_file_size"]
