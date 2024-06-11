import requests
from django.conf import settings
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.models.integrations.googledrive.googledrive_oauth_state import (
    GoogleDriveOAuthState,
)
from api.models.integrations.googledrive.googledrive_user import GoogleDriveUser
from api.serializers.integrations.googledrive.googledrive_oauth import (
    GoogleDriveOauthRedirectSerializer,
)


class GoogleDriveOauthRedirectView(generics.CreateAPIView):
    serializer_class = GoogleDriveOauthRedirectSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        state = request.data["data"].get("state")
        code = request.data["data"].get("code")
        project_id = kwargs.get("project_id")
        print(f"state to check={state}")
        print(f"code to exchange={code}")
        print(f"project_id={project_id}")

        try:
            oauth_state = GoogleDriveOAuthState.objects.get(
                state=state, user=request.user
            )
        except GoogleDriveOAuthState.DoesNotExist:
            raise ValidationError("Invalid state parameter")

        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        response = requests.post("https://oauth2.googleapis.com/token", data=data)
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content.decode('utf-8')}")
        tokens = response.json()

        GoogleDriveUser.objects.create(
            user=request.user,
            project_id=project_id,
            access_token=tokens["access_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
        )

        oauth_state.delete()
        return Response({"success": True})
