from django.db import models
from django.db.models import Count
from django.db.models.query import QuerySet
from shortuuid.django_fields import ShortUUIDField
from pgvector.django import HnswIndex, VectorField

from api.models.project import Project
from api.models.tag_board import TagBoard


class TagModelManager(models.Manager):
    def get_queryset(self) -> QuerySet:
        return (
            super()
            .get_queryset()
            .annotate(takeaway_count=Count("takeaways", distinct=True))
        )


class Tag(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    vector = VectorField(dimensions=1536)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, blank=True)  # Assuming color in hexadecimal format
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tag_board = models.ForeignKey(TagBoard, on_delete=models.SET_NULL, related_name='tags', null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tags", editable=False)
    objects = TagModelManager()

    class Meta:
        unique_together = [["name", "tag_board"]]
        indexes = [
            HnswIndex(
                name="tag-vector-index",
                fields=["vector"],
                opclasses=["vector_ip_ops"],  # Use the inner product operator
            )
        ]

    def __str__(self):
        return self.name
