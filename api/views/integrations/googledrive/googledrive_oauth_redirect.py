from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers.integrations.googledrive.googledrive_oauth import (
    GoogleDriveOauthRedirectSerializer,
)


class GoogleDriveOauthRedirectView(generics.CreateAPIView):
    serializer_class = GoogleDriveOauthRedirectSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data.get("data", request.data)
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)
        serializer.save()
        return Response({"status": "Success"})
