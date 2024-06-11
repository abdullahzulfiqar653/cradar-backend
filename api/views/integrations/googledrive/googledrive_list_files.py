import requests
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models.integrations.googledrive.googledrive_user import GoogleDriveUser


class GoogleDriveListFilesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            gdrive_user = GoogleDriveUser.objects.get(user=request.user)
        except GoogleDriveUser.DoesNotExist:
            raise ValidationError("Google Drive account not connected")

        headers = {"Authorization": f"Bearer {gdrive_user.access_token}"}

        response = requests.get(
            "https://www.googleapis.com/drive/v3/files", headers=headers
        )

        if response.status_code != 200:
            print(headers)
            print(response.json())
            raise ValidationError("Failed to retrieve files from Google Drive")

        files = response.json().get("files", [])
        return Response(files)
