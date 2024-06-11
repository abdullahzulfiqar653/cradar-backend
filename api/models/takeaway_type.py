from django.db import models
from pgvector.django import HnswIndex, VectorField
from shortuuid.django_fields import ShortUUIDField

from api.models.project import Project

default_takeaway_types = [
    "Pain Point",
    "Aha Moment",
    "Feature Request",
    "Churn Signal",
    "Price Mention",
    "Competitor Mention",
]


class TakeawayType(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    vector = VectorField(dimensions=1536)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="takeaway_types", editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["project", "name"]]
        indexes = [
            HnswIndex(
                name="note-type-vector-index",
                fields=["vector"],
                opclasses=["vector_ip_ops"],  # Use the inner product operator
            )
        ]

    def __str__(self) -> str:
        return self.name
