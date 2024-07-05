from django.db import models
from ordered_model.models import OrderedModel
from shortuuid.django_fields import ShortUUIDField

from api.models.note import Note
from api.models.user import User


class Message(OrderedModel):
    class Role(models.TextChoices):
        SYSTEM = "system"
        HUMAN = "human"
        AI = "ai"

    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    note = models.ForeignKey(
        Note, on_delete=models.CASCADE, related_name="messages", editable=False
    )
    role = models.CharField(max_length=6, choices=Role.choices, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order_with_respect_to = "note"

    class Meta:
        ordering = ["user", "order"]

    def __str__(self):
        return f"{self.user} - {self.text[:50]}"
