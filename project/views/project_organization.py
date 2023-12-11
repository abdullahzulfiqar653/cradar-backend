from rest_framework import exceptions, generics

from note.models.organization import Organization
from note.serializers.organization import OrganizationSerializer


class ProjectOrganizationListView(generics.ListAPIView):
    serializer_class = OrganizationSerializer
    queryset = Organization.objects.all()
    ordering = ["name"]
    search_fields = ["name"]

    def get_queryset(self):
        project_id = self.kwargs["project_id"]
        project = self.request.user.projects.filter(id=project_id).first()
        if project is None:
            raise exceptions.NotFound

        return Organization.objects.filter(project=project_id)
