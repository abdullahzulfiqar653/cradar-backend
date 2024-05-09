from rest_framework import exceptions, generics

from api.models.note_template import NoteTemplate
from api.serializers.note_template import (
    NoteTemplateDetailSerializer,
    NoteTemplateSerializer,
)


class ProjectNoteTemplateListCreateView(generics.ListCreateAPIView):
    queryset = NoteTemplate.objects.none()
    search_fields = ["title", "questions__title"]

    def get_queryset(self):
        public_note_templates = NoteTemplate.objects.filter(project__isnull=True)
        project_note_templates = self.request.project.note_templates.all()
        return public_note_templates.union(project_note_templates)

    def get_serializer_class(self):
        match self.request.method:
            case "GET":
                return NoteTemplateSerializer
            case "POST":
                return NoteTemplateDetailSerializer
            case _:
                raise exceptions.MethodNotAllowed("Only GET and POST are allowed.")
