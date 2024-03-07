from rest_framework import generics

from api.models.block import Block
from api.serializers.block import BlockSerializer


class BlockRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Block.objects.all()
    serializer_class = BlockSerializer
