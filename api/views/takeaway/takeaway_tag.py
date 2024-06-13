from rest_framework import generics, status
from rest_framework.response import Response

from api.serializers.tag import TagSerializer


class TakeawayTagCreateView(generics.CreateAPIView):
    serializer_class = TagSerializer


class TakeawayTagDestroyView(generics.DestroyAPIView):

    def destroy(self, request, takeaway_id, tag_id):
        tag = request.takeaway.tags.filter(id=tag_id).first()
        if tag:
            request.takeaway.tags.remove(tag)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_404_NOT_FOUND)
