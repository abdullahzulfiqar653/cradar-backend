from django.db import models
from shortuuid.django_fields import ShortUUIDField

from api.models.project import Project
from api.models.question import Question


class NoteTemplate(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="note_templates", null=True
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    questions = models.ManyToManyField(
        Question, related_name="note_templates", through="api.NoteTemplateQuestion"
    )
    type = models.ForeignKey(
        "api.NoteTemplateType",
        on_delete=models.SET_NULL,
        related_name="note_templates",
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title
