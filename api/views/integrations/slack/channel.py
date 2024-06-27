import requests
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers.integrations.slack.channel import ListChannelsSerializer


@extend_schema(
    responses=ListChannelsSerializer,
)
class SlackChannelsListView(generics.ListAPIView):
    "Calling SlackChannelsList"
    serializer_class = ListChannelsSerializer
    # TODO: Update to the proper permission class
    permission_classes = [IsAuthenticated]

    def get_channels(self):
        slack_users = self.request.user.slack_users.all()
        if not slack_users.exists():
            return []
        all_channels = []
        for slack_user in slack_users:
            headers = {"Authorization": f"Bearer {slack_user.access_token}"}
            params = {"types": "public_channel,private_channel"}
            response = requests.get(
                "https://slack.com/api/conversations.list",
                headers=headers,
                params=params,
            )
            if response.status_code == 200:
                channels = [
                    channel
                    for channel in response.json().get("channels", [])
                    if channel.get("is_member", True)
                ]
                all_channels.extend(channels)

        return all_channels

    def list(self, request, *args, **kwargs):
        channels = self.get_channels()
        data = {"channels": channels}
        serializer = self.get_serializer(data)
        return Response(serializer.data)
