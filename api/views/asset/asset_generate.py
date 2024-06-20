from django.http import QueryDict
from pgvector.django import MaxInnerProduct
from rest_framework import generics

from api.ai.embedder import embedder
from api.ai.generators.block_generator import generate_content
from api.filters.takeaway import TakeawayFilter
from api.models.takeaway import Takeaway
from api.serializers.asset import AssetGenerateSerializer


class AssetGenerateCreateView(generics.CreateAPIView):
    serializer_class = AssetGenerateSerializer

    # The following are for filtering takeaways
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

    def perform_create(self, serializer):
        asset = self.request.asset

        # Filter takeaways
        filter_string = self.request.data.get("filter")
        if filter_string is None:
            filter_string = asset.filter
        self.request._request.GET = QueryDict(filter_string)
        takeaways = Takeaway.objects.filter(note__project=self.request.asset.project)
        takeaways = self.filter_queryset(takeaways)

        question = self.request.data["question"]
        vector = embedder.embed_query(question)
        takeaways = takeaways.order_by(MaxInnerProduct("vector", vector))

        output = generate_content(asset, question, takeaways, self.request.user)
        serializer.validated_data["markdown"] = output
