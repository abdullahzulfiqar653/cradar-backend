from rest_framework import generics
from api.models.tag import Tag
from api.serializers.tag import TagSerializer


class TagRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
