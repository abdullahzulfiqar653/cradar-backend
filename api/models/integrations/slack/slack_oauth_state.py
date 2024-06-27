import secrets

from django.db import models
from django.utils import timezone

from api.models.user import User


class SlackOAuthState(models.Model):
    state = models.CharField(max_length=100, unique=True, default=secrets.token_urlsafe)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    @property
    def is_expired(self):
        return timezone.now() - self.created_at > timezone.timedelta(minutes=10)
