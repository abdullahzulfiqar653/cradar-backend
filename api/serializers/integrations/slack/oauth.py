import requests
from django.conf import settings
from drf_spectacular.utils import extend_schema_field
from rest_framework import exceptions, serializers

from api.models.integrations.slack.slack_oauth_state import SlackOAuthState
from api.models.integrations.slack.slack_user import SlackUser


class SlackOauthUrlSerializer(serializers.Serializer):
    url = serializers.SerializerMethodField()

    def create_slack_state(self, user=None):
        state = SlackOAuthState(user=user)
        state.save()
        return state

    @extend_schema_field(serializers.CharField)
    def get_url(self, obj) -> str:
        user = self.context["request"].user
        state = self.create_slack_state(user if user.is_authenticated else None)

        slack_oauth_url = (
            f"https://slack.com/oauth/v2/authorize"
            f"?client_id={settings.SLACK_CLIENT_ID}"
            f"&scope=channels:history,groups:history,im:history,mpim:history,channels:read,groups:read,mpim:read,im:read"
            f"&user_scope="
            f"&state={state.state}"
            f"&redirect_uri={settings.SLACK_REDIRECT_URI}"
        )
        return slack_oauth_url

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.is_authenticated:
            raise exceptions.ValidationError(
                "User must be logged in to initiate Slack integration."
            )
        if not settings.SLACK_CLIENT_ID or not settings.SLACK_REDIRECT_URI:
            raise exceptions.ValidationError(
                "Slack client configuration is incomplete."
            )
        return attrs

    def create(self, validated_data):
        return {"url": self.get_url(None)}


class SlackOAuthRedirectSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)
    state = serializers.CharField(required=True)

    def validate(self, data):
        code = data.get("code")
        state = data.get("state")

        # Validate the state
        oauth_state = SlackOAuthState.objects.filter(state=state).first()
        if not oauth_state:
            raise exceptions.ValidationError({"state": "Invalid state parameter."})

        if oauth_state.is_expired:
            oauth_state.delete()
            raise exceptions.ValidationError({"state": "State has expired."})

        # Perform the Slack OAuth request
        response = requests.post(
            "https://slack.com/api/oauth.v2.access",
            data={
                "client_id": settings.SLACK_CLIENT_ID,
                "client_secret": settings.SLACK_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.SLACK_REDIRECT_URI,
            },
        )
        response_data = response.json()

        if not response_data.get("ok"):
            raise exceptions.ValidationError({"slack": "Authentication failed."})

        data["response"] = response_data
        return data

    def save(self, **kwargs):
        data = self.validated_data
        response_data = data["response"]
        user = self.context["request"].user

        # Create or update the SlackUser instance
        SlackUser.objects.update_or_create(
            user=user,
            slack_team_id=response_data["team"]["id"],
            defaults={
                "access_token": response_data["access_token"],
                "slack_user_id": response_data["authed_user"]["id"],
                "bot_user_token": response_data.get("bot_user_id", ""),
            },
        )

        # Delete the OAuth state after successful processing
        oauth_state = SlackOAuthState.objects.get(state=data.get("state"))
        oauth_state.delete()
