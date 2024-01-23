from django.db import models
from shortuuid.django_fields import ShortUUIDField

from api.models.tag import Tag
from api.models.user import User


class Takeaway(models.Model):
    class Priority(models.TextChoices):
        LOW = "Low"
        MED = "Med"
        HIGH = "High"

    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    title = models.TextField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="takeaways")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_takeaways",
        related_query_name="created_takeaways",
    )
    upvoted_by = models.ManyToManyField(
        User, related_name="upvoted_takeaways", related_query_name="upvoted_takeaways"
    )
    priority = models.CharField(max_length=4, choices=Priority.choices, null=True)
    note = models.ForeignKey(
        "api.Note", on_delete=models.CASCADE, related_name="takeaways"
    )
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.code == "":
            self.code = f"{self.note.code}-{self.note.takeaway_sequence + 1}"
            note = self.note
            note.takeaway_sequence += 1
            note.save()
        super().save(*args, **kwargs)