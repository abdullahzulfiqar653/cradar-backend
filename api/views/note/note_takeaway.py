from rest_framework import generics

from api.filters.takeaway import NoteTakeawayFilter
from api.models.takeaway import Takeaway
from api.serializers.takeaway import TakeawaySerializer


class NoteTakeawayListCreateView(generics.ListCreateAPIView):
    queryset = Takeaway.objects.all()
    serializer_class = TakeawaySerializer
    filterset_class = NoteTakeawayFilter
    ordering_fields = [
        "created_at",
        "created_by__first_name",
        "created_by__last_name",
        "title",
    ]
    ordering = ["created_at"]
    search_fields = [
        "title",
        "highlight__quote",
        "created_by__username",
        "created_by__first_name",
        "created_by__last_name",
    ]
    query_field = "vector"

    def get_queryset(self):
        return TakeawaySerializer.optimize_query(
            self.request.note.takeaways.all(), self.request.user
        )
