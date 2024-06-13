from rest_framework import generics
from api.serializers.tag_board import TagBoardSerializer


class ProjectTagBoardListCreateView(generics.ListCreateAPIView):
    serializer_class = TagBoardSerializer

    def get_queryset(self):
        return self.request.project.tag_boards.all()
