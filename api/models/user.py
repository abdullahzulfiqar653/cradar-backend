from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

# Create your models here.


class CustomUserManager(UserManager):
    def get_by_natural_key(self, username: str | None):
        return self.get(username__iexact=username)


class User(AbstractUser):
    skip_tutorial = models.BooleanField(default=False)
    consent_given = models.BooleanField(default=False)
    job = models.CharField(max_length=100, blank=True)
    saved_takeaways = models.ManyToManyField(
        "api.Takeaway", related_name="saved_by", through="api.UserSavedTakeaway"
    )
    tutorial = models.JSONField(default=dict)
    objects = CustomUserManager()

    def get_role(self, workspace):
        try:
            return self.workspace_users.get(workspace=workspace).role
        except models.ObjectDoesNotExist:
            return None
