from rest_framework import generics, status
from rest_framework.response import Response

from api.permissions import IsWorkspaceOwner
from api.serializers.user import UsersSerializer


class ProjectUserDeleteView(generics.CreateAPIView):
    serializer_class = UsersSerializer
    permission_classes = [IsWorkspaceOwner]

    def post(self, request, project_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usernames = [user["username"] for user in serializer.data["users"]]
        users = self.request.project.users.filter(username__in=usernames)
        self.request.project.users.remove(*users)
        response_serializer = self.get_serializer({"users": users})
        return Response(response_serializer.data, status=status.HTTP_200_OK)
