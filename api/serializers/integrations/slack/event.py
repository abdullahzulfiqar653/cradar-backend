import hashlib
import hmac

import requests
from django.conf import settings
from django.utils.timezone import datetime, make_aware
from rest_framework import exceptions, serializers

from api.models.integrations.slack.slack_message_buffer import SlackMessageBuffer
from api.models.integrations.slack.slack_user import SlackUser


class SlackEventSerializer(serializers.Serializer):
    type = serializers.CharField()
    token = serializers.CharField()
    challenge = serializers.CharField(required=False)
    event = serializers.JSONField(required=False)

    def verify_slack_request(self, request):
        # Ref: https://api.slack.com/authentication/verifying-requests-from-slack#validating-a-request
        slack_signing_secret = bytes(settings.SLACK_SIGNING_SECRET, "utf-8")
        raw_body = self.context.get("raw_body")
        timestamp = request.headers.get("X-Slack-Request-Timestamp")
        signature = request.headers.get("X-Slack-Signature")

        basestring = f"v0:{timestamp}:{raw_body}".encode("utf-8")
        my_signature = (
            "v0="
            + hmac.new(slack_signing_secret, basestring, hashlib.sha256).hexdigest()
        )
        return hmac.compare_digest(my_signature, signature)

    def fetch_slack_username(self, slack_user_token, user_id):
        url = "https://slack.com/api/users.info"
        headers = {"Authorization": f"Bearer {slack_user_token}"}
        params = {"user": user_id}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            user_info = response.json()
            if user_info.get("ok"):
                return user_info["user"]["name"]
        return None

    def handle_message_event(self, event):
        slack_channel_id = event.get("channel")
        slack_team_id = event.get("team")
        slack_user_id = event.get("user")
        message_text = event.get("text", "[No message text found]")
        timestamp = make_aware(datetime.fromtimestamp(float(event.get("ts"))))

        # Fetch the SlackUser object
        slack_user = SlackUser.objects.filter(slack_team_id=slack_team_id).first()
        if slack_user:
            username = self.fetch_slack_username(slack_user.access_token, slack_user_id)
        else:
            username = "Unknown User"

        # Create a record in the SlackMessageBuffer
        SlackMessageBuffer.objects.create(
            slack_channel_id=slack_channel_id,
            slack_team_id=slack_team_id,
            slack_user=username or slack_user_id,
            message_text=message_text,
            timestamp=timestamp,
        )
        return True

    def validate(self, data):
        request = self.context.get("request")
        if not self.verify_slack_request(request):
            raise exceptions.ValidationError("Invalid request.")

        if data.get("type") == "url_verification":
            return data

        if data.get("type") == "event_callback":
            event = data.get("event", {})
            if event.get("type") == "message" and not event.get("subtype", None):
                self.handle_message_event(event)

        return data
