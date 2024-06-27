from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from api.models.workspace import Workspace
from api.models.workspace_user import WorkspaceUser
from api.permissions import IsWorkspaceMemberReadOnly, IsWorkspaceOwner
from api.serializers.user import WorkspaceUserSerializer
from api.serializers.workspace import WorkspaceSerializer


class WorkspaceUserListUpdateView(generics.ListAPIView, generics.UpdateAPIView):
    queryset = WorkspaceUser.objects.all()
    serializer_class = WorkspaceUserSerializer
    permission_classes = [IsWorkspaceOwner | IsWorkspaceMemberReadOnly]

    def get_queryset(self):
        return WorkspaceUser.objects.filter(workspace=self.request.workspace)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        username = self.request.data.get("username")
        obj = generics.get_object_or_404(
            queryset, user__username=username, workspace=self.request.workspace
        )
        self.check_object_permissions(self.request, obj)
        return obj


class WorkspaceListCreateView(generics.ListCreateAPIView):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.workspaces.all()
