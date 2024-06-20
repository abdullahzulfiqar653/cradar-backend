from django.db.models import Count
from rest_framework import generics

from api.models.note_type import NoteType
from api.serializers.note_type import ProjectNoteTypeSerializer


class ProjectNoteTypeListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectNoteTypeSerializer
    queryset = NoteType.objects.all()
    ordering = ["-report_count", "name"]
    search_fields = ["name"]
    query_field = "vector"

    def get_queryset(self):
        return self.request.project.note_types.annotate(report_count=Count("notes"))
