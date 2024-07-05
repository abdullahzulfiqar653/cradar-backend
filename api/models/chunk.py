from django.contrib.postgres.indexes import HashIndex
from django.db import models
from pgvector.django import HnswIndex, VectorField
from shortuuid.django_fields import ShortUUIDField


class Chunk(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    text = models.TextField()
    note = models.ForeignKey("Note", on_delete=models.CASCADE, related_name="chunks")
    vector = VectorField(dimensions=1536)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            HashIndex(fields=["text"]),
            HnswIndex(
                name="chunk-vector-index",
                fields=["vector"],
                opclasses=["vector_ip_ops"],  # Use the inner product operator
            ),
        ]
