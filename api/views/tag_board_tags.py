from rest_framework import generics
from api.serializers.tag import TagSerializer


class TagBoardTagsListCreateView(generics.ListCreateAPIView):
    serializer_class = TagSerializer

    def get_queryset(self):
        return self.request.tag_board.tags.all()
