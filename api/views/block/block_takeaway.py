from rest_framework import generics, status
from rest_framework.response import Response

from api.models.block import Block
from api.models.takeaway import Takeaway
from api.serializers.takeaway import BlockTakeawaysSerializer, TakeawaySerializer


class BlockTakeawayListCreateView(generics.ListCreateAPIView):
    queryset = Takeaway.objects.all()

    def get_serializer_class(self):
        match self.request.method:
            case "GET":
                return TakeawaySerializer
            case "POST":
                return BlockTakeawaysSerializer

    def get_queryset(self):
        return self.request.block.takeaways.all()

    def get_valid_takeaways(self, block: Block):
        # Can add or remove any takeaways in the project to the block
        return Takeaway.objects.filter(note__project=block.asset.project)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        valid_takeaways = self.get_valid_takeaways(self.request.block)
        context["block"] = self.request.block
        context["valid_takeaway_ids"] = valid_takeaways.values_list("id", flat=True)
        return context


class BlockTakeawayDeleteView(generics.GenericAPIView):
    queryset = Takeaway.objects.all()
    serializer_class = BlockTakeawaysSerializer

    def get_valid_takeaways(self, block: Block):
        # Can add or remove any takeaways in the project to the block
        return Takeaway.objects.filter(note__project=block.asset.project)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        valid_takeaways = self.get_valid_takeaways(self.request.block)
        context["block"] = self.request.block
        context["valid_takeaway_ids"] = valid_takeaways.values_list("id", flat=True)
        return context

    def post(self, request, block_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.delete()
        return Response(serializer.data, status=status.HTTP_200_OK)
