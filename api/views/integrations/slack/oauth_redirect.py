from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers.integrations.slack.oauth import SlackOAuthRedirectSerializer


class SlackOauthRedirectCreateView(generics.CreateAPIView):
    serializer_class = SlackOAuthRedirectSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = SlackOAuthRedirectSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"status": "Success"})
