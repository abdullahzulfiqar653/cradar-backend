from django.db import models
from shortuuid.django_fields import ShortUUIDField

from api.models.note import Note
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class TranscriptionUsage(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="transcription_usages"
    )
    # We use set_null for the following fields
    # so that the costs are still counted even when the projects or created_by are deleted
    project = models.ForeignKey(
        Project,
        null=True,
        on_delete=models.SET_NULL,
        related_name="transcription_usages",
    )
    note = models.ForeignKey(
        Note, null=True, on_delete=models.SET_NULL, related_name="transcription_usages"
    )
    created_by = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, related_name="transcription_usages"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    value = models.IntegerField(help_text="Audio file duration in seconds")
    cost = models.DecimalField(default=0, decimal_places=7, max_digits=11)
