from django.http import QueryDict
from rest_framework.generics import CreateAPIView

from api.ai.generators.block_clusterer import cluster_block
from api.filters.takeaway import TakeawayFilter
from api.models.takeaway import Takeaway
from api.serializers.block import BlockThemeSerializer


class BlockClusterCreateView(CreateAPIView):
    serializer_class = BlockThemeSerializer

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
        "highlight__quote",
        "created_by__username",
        "created_by__first_name",
        "created_by__last_name",
    ]

    def perform_create(self, serializer):
        block = self.request.block

        # Filter takeaways
        filter_string = serializer.data.get("filter", "")
        block.filter = filter_string
        self.request._request.GET = QueryDict(filter_string)
        takeaways = Takeaway.objects.filter(note__assets=block.asset)
        takeaways = self.filter_queryset(takeaways)
        cluster_block(block, takeaways, self.request.user)
