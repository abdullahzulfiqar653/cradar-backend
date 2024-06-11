from django.conf import settings
from django.db import models


class GoogleDriveOAuthState(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    state = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
