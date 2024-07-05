from rest_framework import generics

from api.models.message import Message
from api.serializers.message import MessageSerializer


class NoteMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    queryset = Message.objects.all()
    ordering = ["order"]

    def get_queryset(self):
        return self.request.note.messages.all()
