from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response

from api.ai.generators.tag_generator import generate_tags


@extend_schema(request=None, responses={200: None})
class NoteTagGenerateView(generics.CreateAPIView):
    def create(self, request, report_id):
        note = request.note

        # Call OpenAI
        try:
            generate_tags(note, created_by=self.request.user)
        except Exception as e:
            return Response(
                {"details": "Failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({"details": "Successful"})
