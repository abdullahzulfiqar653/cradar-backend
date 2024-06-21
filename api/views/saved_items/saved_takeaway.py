from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.filters.takeaway import TakeawayFilter
from api.models.takeaway import Takeaway
from api.serializers.takeaway import SavedTakeawaysSerializer, TakeawaySerializer


class SavedTakeawayListCreateView(generics.ListCreateAPIView):
    queryset = Takeaway.objects.all()
    serializer_class = TakeawaySerializer
    filterset_class = TakeawayFilter
    permission_classes = [IsAuthenticated]
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
                return SavedTakeawaysSerializer

    def get_queryset(self):
        return TakeawaySerializer.optimize_query(
            Takeaway.objects.filter(saved_by=self.request.user).filter(
                note__project__users=self.request.user
            ),
            self.request.user,
        )

    def get_valid_takeaways(self):
        # Can add or remove any takeaways in the project that the user is in
        return Takeaway.objects.filter(note__project__users=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        valid_takeaways = self.get_valid_takeaways()
        context["user"] = self.request.user
        context["valid_takeaway_ids"] = valid_takeaways.values_list("id", flat=True)
        return context


class SavedTakeawayDeleteView(generics.GenericAPIView):
    queryset = Takeaway.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = SavedTakeawaysSerializer

    def get_valid_takeaways(self):
        # Can add or remove any takeaways in the project that the user is in
        return Takeaway.objects.filter(note__project__users=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        valid_takeaways = self.get_valid_takeaways()
        context["user"] = self.request.user
        context["valid_takeaway_ids"] = valid_takeaways.values_list("id", flat=True)
        return context

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.delete()
        return Response(serializer.data, status=status.HTTP_200_OK)
