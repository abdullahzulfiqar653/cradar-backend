from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.text import slugify
from shortuuid.django_fields import ShortUUIDField

from api.models.user import User


class Workspace(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owned_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="owned_workspaces"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    logo_url = models.URLField(blank=True)
    domain_slug = models.SlugField(max_length=50, unique=True)

    members = models.ManyToManyField(User, related_name="workspaces")

    @property
    def usage_seconds(self):
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        return (
            self.transcription_usages.filter(created_at__gt=start_of_month)
            .aggregate(value=Coalesce(Sum("value"), 0))
            .get("value")
        )

    @property
    def usage_tokens(self):
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        return (
            self.token_usages.filter(created_at__gt=start_of_month)
            .aggregate(value=Coalesce(Sum("value"), 0))
            .get("value")
        )

    @property
    def total_file_size(self):
        return self.notes.aggregate(value=Sum("file_size")).get("value")

    def __str__(self):
        return f"{self.id} - {self.name}"

    def save(self, *args, **kwargs):
        # Generate the domain slug based on the workspace name
        self.domain_slug = slugify(self.name)
        super().save(*args, **kwargs)
