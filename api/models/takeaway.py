from django.db import models
from pgvector.django import HnswIndex, VectorField
from shortuuid.django_fields import ShortUUIDField

from api.models.tag import Tag
from api.models.takeaway_type import TakeawayType
from api.models.user import User


class Takeaway(models.Model):
    class Priority(models.TextChoices):
        LOW = "Low"
        MED = "Med"
        HIGH = "High"

    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    title = models.TextField()
    description = models.TextField(blank=True)
    vector = VectorField(dimensions=1536)
    type = models.ForeignKey(
        TakeawayType, on_delete=models.SET_NULL, related_name="takeaways", null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
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

    class Meta:
        indexes = [
            HnswIndex(
                name="takeaway-vector-index",
                fields=["vector"],
                opclasses=["vector_ip_ops"],  # Use the inner product operator
            )
        ]

    def __str__(self):
        return self.title
