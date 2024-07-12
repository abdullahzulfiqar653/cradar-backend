# workspace/serializers.py
from django.db.models import Q
from django.utils.text import slugify
from rest_framework import exceptions, serializers

from api.mixpanel import mixpanel
from api.models.feature import Feature
from api.models.workspace import Workspace


class WorkspaceSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=100)
    is_owner = serializers.BooleanField(read_only=True)
    subscription_end_at = serializers.CharField(
        source="subscription.end_at", read_only=True
    )
    subscription_is_free_trial = serializers.BooleanField(
        source="subscription.is_free_trial", read_only=True
    )
    subscription_name = serializers.CharField(
        source="subscription.product.name", read_only=True
    )
    subscription_type = serializers.SerializerMethodField()

    def get_subscription_type(self, workspace) -> str:
        if hasattr(workspace, "subscription"):
            return workspace.subscription.product.usage_type
        return ""

    class Meta:
        model = Workspace
        fields = [
            "id",
            "name",
            "is_owner",
            "industry",
            "company_size",
            "subscription_type",
            "subscription_name",
            "subscription_end_at",
            "subscription_is_free_trial",
        ]

    def validate_name(self, value):
        name = value
        slug = slugify(name)
        condition = Q(name__iexact=name) | Q(domain_slug=slug)
        if name and Workspace.objects.filter(condition).exists():
            raise serializers.ValidationError(f"Workspace Name already taken.")
        return value

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user

        if user.owned_workspaces.count() > 1:
            raise exceptions.PermissionDenied(
                "You have reached your quota limit and cannot create more workspaces."
            )

        validated_data["owned_by"] = user
        workspace = super().create(validated_data)
        user.workspaces.add(workspace, through_defaults={"role": "Owner"})

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
    editors = serializers.SerializerMethodField()
    projects = serializers.SerializerMethodField()
    usage_minutes = serializers.SerializerMethodField()
    knowledge_sources = serializers.SerializerMethodField()
    usage_minutes_limit = serializers.SerializerMethodField()
    storage_usage_limit = serializers.SerializerMethodField()

    def get_usage_minutes(self, workspace) -> int:
        return round(workspace.usage_seconds / 60)

    def get_usage_minutes_limit(self, workspace) -> int:
        return workspace.get_feature_value(Feature.Code.DURATION_MINUTE_WORKSPACE)

    def get_storage_usage_limit(self, workspace) -> int:
        return (
            workspace.get_feature_value(Feature.Code.STORAGE_GB_WORKSPACE)
            * 1024
            * 1024
            * 1024
        )

    def get_projects(self, workspace: Workspace) -> dict:
        return {
            "quota": workspace.get_feature_value(Feature.Code.NUMBER_OF_PROJECTS),
            "usage": workspace.projects.count(),
        }

    def get_editors(self, workspace: Workspace) -> dict:
        return {
            "quota": workspace.get_feature_value(Feature.Code.NUMBER_OF_EDITORS),
            "usage": workspace.workspace_users.count(),
        }

    def get_knowledge_sources(self, workspace: Workspace) -> dict:
        return {
            "quota": workspace.get_feature_value(
                Feature.Code.NUMBER_OF_KNOWLEDGE_SOURCES
            ),
            "usage": workspace.notes.count(),
        }

    class Meta:
        model = Workspace
        fields = WorkspaceSerializer.Meta.fields + [
            "editors",
            "projects",
            "usage_tokens",
            "usage_minutes",
            "total_file_size",
            "knowledge_sources",
            "usage_minutes_limit",
            "storage_usage_limit",
        ]
