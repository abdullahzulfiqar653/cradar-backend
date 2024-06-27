from rest_framework import exceptions, generics, status
from rest_framework.response import Response

from api.filters.takeaway import TakeawayFilter
from api.models.insight import Insight
from api.models.takeaway import Takeaway
from api.serializers.takeaway import InsightTakeawaysSerializer, TakeawaySerializer


class InsightTakeawayListCreateView(generics.ListCreateAPIView):
    queryset = Takeaway.objects.all()
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
        "highlight__quote",
        "created_by__username",
        "created_by__first_name",
        "created_by__last_name",
    ]

    def get_serializer_class(self):
        match self.request.method:
            case "GET":
                return TakeawaySerializer
            case "POST":
                return InsightTakeawaysSerializer
            case _:
                raise exceptions.MethodNotAllowed("Only GET and POST are allowed.")

    def get_queryset(self):
        return TakeawaySerializer.optimize_query(
            self.request.insight.takeaways.all(), self.request.user
        )

    def get_valid_takeaways(self, insight: Insight):
        # Can add or remove any takeaways in the project to the insight
        return Takeaway.objects.filter(note__project=insight.project)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        valid_takeaways = self.get_valid_takeaways(self.request.insight)
        context["insight"] = self.request.insight
        context["valid_takeaway_ids"] = valid_takeaways.values_list("id", flat=True)
        return context


class InsightTakeawayDeleteView(generics.GenericAPIView):
    queryset = Takeaway.objects.all()
    serializer_class = InsightTakeawaysSerializer

    def get_valid_takeaways(self, insight: Insight):
        # Can add or remove any takeaways in the project to the insight
        return Takeaway.objects.filter(note__project=insight.project)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        valid_takeaways = self.get_valid_takeaways(self.request.insight)
        context["insight"] = self.request.insight
        context["valid_takeaway_ids"] = valid_takeaways.values_list("id", flat=True)
        return context

    def post(self, request, insight_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.delete()
        return Response(serializer.data, status=status.HTTP_200_OK)
