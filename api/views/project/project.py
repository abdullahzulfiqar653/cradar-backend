from rest_framework import generics

from api.models.project import Project
from api.serializers.project import ProjectDetailSerializer


class ProjectRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectDetailSerializer

    def get_queryset(self):
        return self.request.user.projects
