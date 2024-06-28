# workspace/serializers.py
from django.db.models import Q
from django.utils.text import slugify
from rest_framework import exceptions, serializers

from api.mixpanel import mixpanel
from api.models.workspace import Workspace


class WorkspaceSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=100)
    is_owner = serializers.BooleanField(read_only=True)

    class Meta:
        model = Workspace
        fields = ["id", "name", "is_owner", "usage_type", "industry", "company_size"]

    def validate_name(self, value):
        name = value
        slug = slugify(name)
        condition = Q(name__iexact=name) | Q(domain_slug=slug)
        if name and Workspace.objects.filter(condition).exists():
            raise serializers.ValidationError(f"Workspace Name already taken.")
        return value

    def create(self, validated_data):
        request = self.context["request"]

        if request.user.owned_workspaces.count() > 1:
            raise exceptions.PermissionDenied(
                "You have reached your quota limit and cannot create more workspaces."
            )

        validated_data["owned_by"] = request.user
        workspace = super().create(validated_data)

        request = self.context["request"]
        request.user.workspaces.add(workspace, through_defaults={"role": "Owner"})

        # TODO: To keep track whether it is personal or business plan
        mixpanel.track(
            request.user.id,
            "BE: Workspace Created",
            {"workspace_id": workspace.id, "workspace_name": workspace.name},
        )

        return workspace

    def to_representation(self, instance):
        user = self.context.get("request").user
        instance.is_owner = instance.owned_by == user
        return super().to_representation(instance)


class WorkspaceDetailSerializer(WorkspaceSerializer):
    usage_minutes = serializers.SerializerMethodField()

    def get_usage_minutes(self, workspace) -> int:
        return round(workspace.usage_seconds / 60)

    class Meta:
        model = Workspace
        fields = ["id", "name", "usage_minutes", "usage_tokens", "total_file_size"]
