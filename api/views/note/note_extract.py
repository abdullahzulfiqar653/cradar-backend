from drf_spectacular.utils import extend_schema
from rest_framework import generics, response

from api.tasks import analyze_existing_note


@extend_schema(request=None, responses={200: None})
class NoteExtractCreateView(generics.CreateAPIView):
    def create(self, request, report_id):
        note = request.note
        analyze_existing_note.delay(note.id, self.request.user.id)
        return response.Response({"details": "Job sent"})
