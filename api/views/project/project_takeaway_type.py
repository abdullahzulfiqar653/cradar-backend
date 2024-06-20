from rest_framework import generics

from api.models.takeaway_type import TakeawayType
from api.serializers.takeaway_type import TakeawayTypeSerializer


class ProjectTakeawayTypeListCreateView(generics.ListCreateAPIView):
    serializer_class = TakeawayTypeSerializer
    queryset = TakeawayType.objects.all()
    ordering = ["-created_at", "name"]
    ordering_fields = ["created_at", "name"]
    search_fields = ["name"]
    query_field = "vector"

    def get_queryset(self):
        return self.request.project.takeaway_types.all()
