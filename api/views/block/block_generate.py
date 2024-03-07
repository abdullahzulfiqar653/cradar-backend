from django.http import QueryDict
from rest_framework import generics

from api.ai.generators.block_generator import generate_block
from api.filters.takeaway import TakeawayFilter
from api.models.takeaway import Takeaway
from api.serializers.block import BlockGenerateSerializer


class BlockGenerateCreateView(generics.CreateAPIView):
    serializer_class = BlockGenerateSerializer

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
        block = self.request.block

        # Filter takeaways
        filter_string = serializer.data["filter"]
        if filter_string is None:
            filter_string = block.asset.filter
        self.request._request.GET = QueryDict(filter_string)
        takeaways = Takeaway.objects.filter(
            note__project=self.request.block.asset.project
        )
        takeaways = self.filter_queryset(takeaways)

        # Generate content and update serializer and block attributes
        question = serializer.data["question"]
        # We set the attributes of the block here but save it inside generate_block()
        block.question = question
        block.filter = filter_string
        generate_block(block, question, takeaways)
        serializer._data["content"] = block.content
