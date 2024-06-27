from unittest.mock import MagicMock, patch

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.integrations.slack.slack_oauth_state import SlackOAuthState
from api.models.user import User


class SlackOAuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.force_authenticate(user=self.user)

    @patch(
        "api.models.integrations.slack.slack_oauth_state.SlackOAuthState.save",
        MagicMock(),
    )
    def test_oauth_start_creates_state(self):
        response = self.client.get("/api/integrations/slack/oauth_url/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("state=", response.data["url"])

    @patch("requests.post")
    def test_oauth_callback_validates_state(self, mock_post):
        mock_post.return_value.json.return_value = {
            "ok": True,
            "access_token": "some_access_token",
            "team": {"id": "team_id"},
            "authed_user": {"id": "user_id"},
        }

        # Create a valid state in the database for testing
        valid_state = SlackOAuthState.objects.create(
            user=self.user, state="valid_state123"
        )

        # Test callback with valid state
        response = self.client.post(
            "/api/integrations/slack/oauth_redirect/",
            {"code": "12345", "state": valid_state.state},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            SlackOAuthState.objects.filter(state="valid_state123").exists()
        )

        # Test callback with invalid state
        response = self.client.post(
            "/api/integrations/slack/oauth_redirect/",
            {"code": "12345", "state": "invalid_state123"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
