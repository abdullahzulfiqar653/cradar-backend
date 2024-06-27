from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers.integrations.slack.oauth import SlackOauthUrlSerializer


class SlackOauthUrlRetrieveView(generics.RetrieveAPIView):
    serializer_class = SlackOauthUrlSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = SlackOauthUrlSerializer(data={}, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save())
