import json
import logging
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.integrations.slack.slack_message_buffer import SlackMessageBuffer
from api.models.user import User


class TestSlackEvents(APITestCase):
    def setUp(self):
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.url = reverse("slack_events")
        self.user = User.objects.create_user(username="user", password="password")

        self.valid_token = "valid_token"
        self.signing_secret = bytes("YOUR_SLACK_SIGNING_SECRET", "utf-8")

        self.valid_headers = {
            "HTTP_X_SLACK_REQUEST_TIMESTAMP": str(int(timezone.now().timestamp())),
            "HTTP_X_SLACK_SIGNATURE": "v0=mocked_signature",
        }

        self.message_event = {
            "token": self.valid_token,
            "type": "event_callback",
            "event": {
                "type": "message",
                "channel": "C1234567890",
                "user": "U1234567890",
                "text": "Hello world",
                "ts": "1355517523.000005",
                "team": "T1234567890",
            },
        }

        self.url_verification_event = {
            "token": self.valid_token,
            "type": "url_verification",
            "challenge": "random_challenge_string",
        }

    @patch(
        "api.serializers.integrations.slack.event.SlackEventSerializer.verify_slack_request",
        return_value=True,
    )
    def test_url_verification(self, mock_verify):
        """
        Test URL verification challenge response.
        """
        response = self.client.post(
            self.url,
            data=json.dumps(self.url_verification_event),
            content_type="application/json",
            **self.valid_headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["challenge"], "random_challenge_string")

    @patch(
        "api.serializers.integrations.slack.event.SlackEventSerializer.verify_slack_request",
        return_value=True,
    )
    def test_event_callback_message_handling(self, mock_verify):
        """
        Test handling of message event callback.
        """
        response = self.client.post(
            self.url,
            data=json.dumps(self.message_event),
            content_type="application/json",
            **self.valid_headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(SlackMessageBuffer.objects.exists())
        message = SlackMessageBuffer.objects.first()
        self.assertEqual(message.message_text, "Hello world")
        self.assertEqual(message.slack_channel_id, "C1234567890")

    @patch(
        "api.serializers.integrations.slack.event.SlackEventSerializer.verify_slack_request",
        return_value=False,
    )
    def test_invalid_signature(self, mock_verify):
        response = self.client.post(self.url, data={}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
