from django.contrib.auth.models import User
from django.db import models
from shortuuid.django_fields import ShortUUIDField

from workspace.models import Workspace


class Project(models.Model):
    class Language(models.TextChoices):
        EN = "en"
        ID = "id"
        JA = "ja"
        ES = "es"

    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    users = models.ManyToManyField(User, related_name="projects")
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="projects"
    )
    language = models.CharField(
        max_length=2, choices=Language.choices, default=Language.EN
    )

    def __str__(self):
        return self.name
