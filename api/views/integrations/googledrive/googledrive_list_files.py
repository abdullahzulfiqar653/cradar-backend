import requests
from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models.integrations.googledrive.googledrive_user import GoogleDriveUser
from api.permissions import IsWorkspaceEditor, IsWorkspaceOwner
from api.serializers.integrations.googledrive.googledrive_files import (
    GoogleDriveFileSerializer,
)


class GoogleDriveListFilesView(APIView):
    permission_classes = [IsWorkspaceOwner | IsWorkspaceEditor]

    def get(self, request, *args, **kwargs):
        try:
            gdrive_user = GoogleDriveUser.objects.get(user=request.user)
        except GoogleDriveUser.DoesNotExist:
            raise ValidationError("Google Drive account not connected")

        access_token = gdrive_user.access_token

        if self.is_token_expired(access_token):
            access_token = self.refresh_access_token(gdrive_user)

        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.get(
            "https://www.googleapis.com/drive/v3/files", headers=headers
        )

        if response.status_code != 200:
            raise ValidationError("Failed to retrieve files from Google Drive")

        files = response.json().get("files", [])
        serializer = GoogleDriveFileSerializer(files, many=True)
        return Response(serializer.data)

    def is_token_expired(self, access_token):
        response = requests.get(
            f"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access_token}"
        )
        if response.status_code != 200:
            return True
        token_info = response.json()
        return "error" in token_info

    def refresh_access_token(self, gdrive_user):
        refresh_token = gdrive_user.refresh_token
        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        response = requests.post("https://oauth2.googleapis.com/token", data=data)
        tokens = response.json()

        if "access_token" not in tokens:
            raise ValidationError("Failed to refresh access token")

        gdrive_user.access_token = tokens["access_token"]
        gdrive_user.save()

        return tokens["access_token"]
