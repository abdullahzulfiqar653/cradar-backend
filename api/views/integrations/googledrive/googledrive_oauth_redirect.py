from rest_framework import generics

from api.serializers.integrations.googledrive.googledrive_oauth import (
    GoogleDriveOauthRedirectSerializer,
)


class GoogleDriveOauthRedirectView(generics.CreateAPIView):
    serializer_class = GoogleDriveOauthRedirectSerializer
