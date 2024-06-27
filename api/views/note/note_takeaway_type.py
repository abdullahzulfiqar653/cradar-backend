from rest_framework import generics

from api.models.takeaway_type import TakeawayType
from api.serializers.note_takeaway_type import NoteTakeawayTypeSerializer
from api.serializers.takeaway_type import TakeawayTypeSerializer


class NoteTakeawayTypeListCreateView(generics.ListCreateAPIView):
    queryset = TakeawayType.objects.all()
    ordering = ["-created_at", "name"]
    ordering_fields = ["created_at", "name"]
    search_fields = ["name"]

    def get_serializer_class(self):
        match self.request.method:
            case "POST":
                return NoteTakeawayTypeSerializer
            case _:
                return TakeawayTypeSerializer

    def get_queryset(self):
        return TakeawayType.objects.filter(takeaways__note=self.request.note)
