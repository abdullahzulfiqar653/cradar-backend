from rest_framework import generics

from api.models.block import Block
from api.serializers.block import BlockSerializer


class AssetBlockListCreateView(generics.ListCreateAPIView):
    queryset = Block.objects.all()
    serializer_class = BlockSerializer

    def get_queryset(self):
        return self.request.asset.blocks.all()
