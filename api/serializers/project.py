# api/serializers.py
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from api.ai.embedder import embedder
from api.models.note_type import NoteType, default_note_types
from api.models.project import Project
from api.models.takeaway_type import TakeawayType, default_takeaway_types
from api.serializers.workspace import WorkspaceDetailSerializer, WorkspaceSerializer


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    workspace = WorkspaceSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ["id", "name", "description", "workspace", "language"]

    def create_default_note_types(self, project):
        vectors = embedder.embed_documents(default_note_types)
        NoteType.objects.bulk_create(
            [
                NoteType(name=name, project=project, vector=vector)
                for name, vector in zip(default_note_types, vectors)
            ]
        )

    def create_default_takeaway_types(self, project):
        TakeawayType.objects.bulk_create(
            [
                TakeawayType(
                    name=takeaway_type["name"],
                    definition=takeaway_type["definition"],
                    project=project,
                )
                for takeaway_type in default_takeaway_types
            ]
        )

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        view = self.context.get("view")
        workspace_id = view.kwargs.get("workspace_id")

        workspace = user.workspaces.filter(id=workspace_id).first()
        if workspace is None:
            raise PermissionDenied("Do not have permission to access the workspace.")

        if workspace.projects.count() > 1:
            # We restrict user from creating more than 2 projects per workspace
            raise PermissionDenied("Hit project limit of the workspace.")

        validated_data["workspace"] = workspace
        validated_data["users"] = [user]
        project = super().create(validated_data)
        self.create_default_note_types(project)
        self.create_default_takeaway_types(project)
        return project


class ProjectDetailSerializer(ProjectSerializer):
    workspace = WorkspaceDetailSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ["id", "name", "description", "workspace", "language"]


class ProjectKeyThemeSerializer(serializers.Serializer):
    title = serializers.CharField(read_only=True)
    takeaways = serializers.ListField(child=serializers.CharField())


class ProjectSummarySerializer(serializers.ModelSerializer):
    key_themes = ProjectKeyThemeSerializer(many=True)

    class Meta:
        model = Project
        fields = ["summary", "key_themes"]
