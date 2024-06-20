from django.db import models
from pgvector.django import HnswIndex, VectorField
from shortuuid.django_fields import ShortUUIDField

from api.models.project import Project

default_note_types = [
    "User Interview",
    "Usability Testing",
    "Requirement Gathering",
    "Sales Discovery Call",
    "Demo Meeting",
]


class NoteType(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    vector = VectorField(dimensions=1536)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="note_types", editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["project", "name"]]
        indexes = [
            HnswIndex(
                name="takeaway-type-vector-index",
                fields=["vector"],
                opclasses=["vector_ip_ops"],  # Use the inner product operator
            )
        ]

    def __str__(self) -> str:
        return self.name
