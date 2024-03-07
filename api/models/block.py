from django.db import models
from ordered_model.models import OrderedModel
from shortuuid.django_fields import ShortUUIDField

from api.models.asset import Asset
from api.models.takeaway import Takeaway


class Block(OrderedModel):
    class Type(models.TextChoices):
        TEXT = "Text"
        TAKEAWAYS = "Takeaways"

    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="blocks")
    type = models.CharField(max_length=9, choices=Type.choices)

    # Text block
    question = models.CharField(max_length=255, blank=True)
    content = models.JSONField(null=True)
    filter = models.TextField(default="")

    # Takeaways block
    takeaways = models.ManyToManyField(Takeaway, related_name="blocks")

    order_with_respect_to = "asset"

    class Meta:
        ordering = ("asset", "order")