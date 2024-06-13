from rest_framework import generics
from api.models.tag_board import TagBoard
from api.serializers.tag_board import TagBoardSerializer


class TagBoardRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TagBoardSerializer
    queryset = TagBoard.objects.all()
