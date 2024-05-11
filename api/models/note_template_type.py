from django.db import models
from shortuuid.django_fields import ShortUUIDField

from api.models.project import Project


class NoteTemplateType(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="note_template_types", null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["project", "name"]]

    def __str__(self) -> str:
        return self.name
