from django.db import models
from shortuuid.django_fields import ShortUUIDField

from api.models.project import Project

default_takeaway_types = [
    {
        "name": "Pain Point",
        "definition": "A specific problem or frustration experienced by a customer or user when using a product or service.",
    },
    {
        "name": "Aha Moment",
        "definition": "A point in time when a customer or user suddenly realizes the value or benefit of a product or service, leading to increased engagement and satisfaction.",
    },
    {
        "name": "Feature Request",
        "definition": "A suggestion or demand from a customer or user for a new feature or functionality to be added to a product or service.",
    },
    {
        "name": "Churn Signal",
        "definition": "An indication that a customer or user is likely to stop using a product or service, often based on a decrease in engagement or satisfaction.",
    },
    {
        "name": "Price Mention",
        "definition": "A reference made by a customer or user to the cost or pricing of a product or service, which may indicate price sensitivity or a willingness to pay.",
    },
    {
        "name": "Competitor Mention",
        "definition": "A reference made by a customer or user to a competing product or service, which may indicate a comparison of features, pricing, or overall satisfaction.",
    },
]


class TakeawayType(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    definition = models.CharField(max_length=255)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="takeaway_types", editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["project", "name"]]

    def __str__(self) -> str:
        return self.name
