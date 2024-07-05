from django.db import models
from ordered_model.models import OrderedModel
from shortuuid.django_fields import ShortUUIDField

from api.models.project import Project

default_properties = [
    {
        "name": "Customer Organisation",
        "description": "Name or identification of the customer organization.",
        "data_type": "Text",
    },
    {
        "name": "Revenue Estimation",
        "description": "The impact of the customer on your revenue.",
        "data_type": "Select",
        "options": ["High", "Medium", "Low", "NA"],
    },
    {
        "name": "Impact Estimation",
        "description": "The impact the customer has.",
        "data_type": "Select",
        "options": ["High", "Medium", "Low", "NA"],
    },
]


class Property(OrderedModel):
    class DataType(models.TextChoices):
        TEXT = "Text"
        NUMBER = "Number"
        SELECT = "Select"
        MULTISELECT = "MultiSelect"

    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=100)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="properties", editable=False
    )
    description = models.TextField(blank=True)
    data_type = models.CharField(
        max_length=11, choices=DataType.choices, default=DataType.TEXT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    order_with_respect_to = "project"

    class Meta:
        unique_together = ("name", "project")
        ordering = ("project", "order")

    def __str__(self):
        return f"{self.name}"
