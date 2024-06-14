import uuid

from django.conf import settings
from rest_framework import generics
from rest_framework.response import Response

from api.models.integrations.googledrive.googledrive_oauth_state import (
    GoogleDriveOAuthState,
)
from api.permissions import IsWorkspaceEditor, IsWorkspaceOwner
from api.serializers.integrations.googledrive.googledrive_oauth import (
    GoogleDriveOauthUrlSerializer,
)


class GoogleDriveOauthUrlRetrieveView(generics.RetrieveAPIView):
    serializer_class = GoogleDriveOauthUrlSerializer
    permission_classes = [IsWorkspaceEditor | IsWorkspaceOwner]

    def get(self, request, *args, **kwargs):
        state = str(uuid.uuid4())
        GoogleDriveOAuthState.objects.create(user=request.user, state=state)
        redirect_uri = (
            f"https://accounts.google.com/o/oauth2/auth?"
            f"client_id={settings.GOOGLE_CLIENT_ID}&response_type=code&"
            f"scope={settings.GOOGLE_SCOPES}&redirect_uri={settings.GOOGLE_REDIRECT_URI}&state={state}&"
            f"access_type=offline&prompt=consent"
        )
        return Response({"redirect_uri": redirect_uri})
