from rest_framework import generics

from api.serializers.project_asset_analyze import ProjectAssetAnalyzeSerializer


class ProjectAssetAnalyzeCreateView(generics.CreateAPIView):
    serializer_class = ProjectAssetAnalyzeSerializer
