# api/serializers.py
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from api.ai.embedder import embedder
from api.mixpanel import mixpanel
from api.models import Feature
from api.models.note_type import NoteType, default_note_types
from api.models.option import Option
from api.models.project import Project
from api.models.property import Property, default_properties
from api.models.takeaway_type import TakeawayType, default_takeaway_types
from api.serializers.workspace import WorkspaceDetailSerializer, WorkspaceSerializer


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    workspace = WorkspaceSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ["id", "name", "description", "workspace", "language", "objective"]

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

    def create_default_properties(self, project):
        options_to_create = []
        for property_data in default_properties:
            property = Property.objects.create(
                project=project,
                name=property_data["name"],
                data_type=property_data["data_type"],
                description=property_data["description"],
            )
            for option_name in property_data.get("options", []):
                options_to_create.append(Option(property=property, name=option_name))
        Option.objects.bulk_create(options_to_create)

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        view = self.context.get("view")
        workspace_id = view.kwargs.get("workspace_id")

        workspace = user.workspaces.filter(id=workspace_id).first()
        if workspace is None:
            raise PermissionDenied("Do not have permission to access the workspace.")

        feature_value = workspace.get_feature_value(Feature.Code.NUMBER_OF_PROJECTS)
        if workspace.projects.count() >= feature_value:
            # We limit users to the specified number of projects per workspace.
            raise PermissionDenied("Hit project limit of the workspace.")

        validated_data["workspace"] = workspace
        validated_data["users"] = [user]
        project = super().create(validated_data)
        self.create_default_note_types(project)
        self.create_default_takeaway_types(project)
        self.create_default_properties(project)
        mixpanel.track(
            user.id,
            "BE: Project Created",
            {"project_id": project.id, "project_name": project.name},
        )
        return project


class ProjectDetailSerializer(ProjectSerializer):
    workspace = WorkspaceDetailSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ["id", "name", "description", "workspace", "language", "objective"]


class ProjectKeyThemeSerializer(serializers.Serializer):
    title = serializers.CharField(read_only=True)
    takeaways = serializers.ListField(child=serializers.CharField())


class ProjectSummarySerializer(serializers.ModelSerializer):
    key_themes = ProjectKeyThemeSerializer(many=True)

    class Meta:
        model = Project
        fields = ["summary", "key_themes"]
