from django.db import models
from rest_framework import generics

from api.models.user import User
from api.serializers.user import UserWithWorkspaceOwnerSerializer


class ProjectUserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserWithWorkspaceOwnerSerializer
    ordering = ["last_name"]
    search_fields = [
        "username",
        "first_name",
        "last_name",
    ]

    def get_queryset(self):
        return self.request.project.users.annotate(
            is_workspace_owner=models.Q(
                id=models.Value(self.request.project.workspace.owned_by.id)
            )
        )
