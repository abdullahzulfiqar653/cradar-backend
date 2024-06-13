from django.db import models
from shortuuid.django_fields import ShortUUIDField


class TagBoard(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, blank=True)  # Assuming color in hexadecimal format
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name="tag_boards", editable=False)

    class Meta:
        unique_together = [["name", "project"]]

    def __str__(self):
        return self.name
