from django.db import models
from shortuuid.django_fields import ShortUUIDField

from api.models.asset import Asset
from api.models.takeaway import Takeaway


class Block(models.Model):
    class Type(models.TextChoices):
        TAKEAWAYS = "Takeaways"
        THEMES = "Themes"

    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="blocks")
    type = models.CharField(max_length=9, choices=Type.choices)

    # Takeaways block
    takeaways = models.ManyToManyField(Takeaway, related_name="blocks")

    # Themes block
    filter = models.TextField(default="")
