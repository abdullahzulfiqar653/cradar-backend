from rest_framework import generics, status
from rest_framework.response import Response

from api.models.note import Note
from api.permissions import IsWorkspaceOwner
from api.serializers.user import ProjectUserDeleteSerializer


class ProjectUserDeleteView(generics.CreateAPIView):
    serializer_class = ProjectUserDeleteSerializer
    permission_classes = [IsWorkspaceOwner]

    def post(self, request, project_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usernames = [user["username"] for user in serializer.data["users"]]
        users = self.request.project.users.filter(username__in=usernames)
        self.request.project.users.remove(*users)
        response_serializer = self.get_serializer({"users": users})
        # Fetch notes authored by removed users within the project.
        notes = Note.objects.filter(
            project=self.request.project,
            author__username__in=usernames
        )
        
        # Update channel_id and team_id to null for the fetched notes.
        notes.update(slack_channel_id=None, slack_team_id=None)
        
        # Prepare response data with users removed.
        response_serializer = self.get_serializer({"users": users})
        return Response(response_serializer.data, status=status.HTTP_200_OK)