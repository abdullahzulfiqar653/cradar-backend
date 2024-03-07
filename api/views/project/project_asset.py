from rest_framework import generics

from api.models.asset import Asset
from api.serializers.asset import AssetSerializer


class ProjectAssetListCreateView(generics.ListCreateAPIView):
    serializer_class = AssetSerializer
    queryset = Asset.objects.all()
    ordering_fields = [
        "created_at",
        "created_by__first_name",
        "created_by__last_name",
        "title",
    ]
    search_fields = ["title", "created_by__first_name", "created_by__last_name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return self.request.project.assets.all()
