from rest_framework import generics

from api.models.project import Project
from api.serializers.project import ProjectSerializer


class WorkspaceProjectListCreateView(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        workspace = self.request.workspace
        return Project.objects.filter(workspace=workspace, users=user).select_related(
            "workspace"
        )
