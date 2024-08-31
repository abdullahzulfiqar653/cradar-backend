from django.conf import settings
from django.db import models

from api.models.project import Project


class GoogleDriveCredential(models.Model):
    class TokenType(models.TextChoices):
        ACCESS = "Access"
        REFRESH = "Refresh"
        BEARER = "Bearer"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="google_drive_credentials"
    )
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)
    token_type = models.CharField(max_length=50, choices=TokenType.choices)
    expires_in = models.IntegerField()
