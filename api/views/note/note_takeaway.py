from django.shortcuts import get_object_or_404
from rest_framework import exceptions, generics

from api.filters.takeaway import TakeawayFilter
from api.models.note import Note
from api.models.takeaway import Takeaway
from api.serializers.takeaway import TakeawaySerializer


class NoteTakeawayListCreateView(generics.ListCreateAPIView):
    queryset = Takeaway.objects.all()
    serializer_class = TakeawaySerializer
    filterset_class = TakeawayFilter
    ordering_fields = [
        "created_at",
        "created_by__first_name",
        "created_by__last_name",
        "title",
    ]
    ordering = ["created_at"]
    search_fields = [
        "title",
        "created_by__username",
        "created_by__first_name",
        "created_by__last_name",
    ]

    def get_queryset(self):
        user = self.request.user
        note_id = self.kwargs.get("report_id")
        note = get_object_or_404(Note, id=note_id)
        if not note.project.users.contains(user):
            raise exceptions.PermissionDenied
        return Takeaway.objects.filter(note=note)

    def create(self, request, report_id):
        note = get_object_or_404(Note, id=report_id)
        if not note.project.users.contains(request.user):
            raise exceptions.PermissionDenied
        request.data["note"] = note.id
        return super().create(request)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)