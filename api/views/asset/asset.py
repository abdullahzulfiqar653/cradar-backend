from rest_framework import generics

from api.models.asset import Asset
from api.serializers.asset import AssetSerializer


class AssetRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
