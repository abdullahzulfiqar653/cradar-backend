from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from shortuuid.django_fields import ShortUUIDField

from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class TokenUsage(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="token_usages"
    )
    # We use set_null for the following fields
    # so that the costs are still counted even when the projects or created_by are deleted
    project = models.ForeignKey(
        Project,
        null=True,
        on_delete=models.SET_NULL,
        related_name="token_usages",
    )
    content_type = models.ForeignKey(
        ContentType, null=True, on_delete=models.SET_NULL, related_name="token_usages"
    )
    object_id = models.CharField(max_length=12)
    content_object = GenericForeignKey("content_type", "object_id")
    action = models.CharField()
    created_by = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, related_name="token_usages"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    value = models.IntegerField(help_text="Total number of tokens, input plus output.")
    cost = models.DecimalField(default=0, decimal_places=7, max_digits=11)
