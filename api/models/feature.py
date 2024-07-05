from django.db import models
from shortuuid.django_fields import ShortUUIDField


class Feature(models.Model):
    class Code(models.TextChoices):
        NUMBER_OF_EDITORS = "number-of-editors"
        NUMBER_OF_PROJECTS = "number-of-projects"
        STORAGE_GB_WORKSPACE = "storage-gb-workspace"
        STORAGE_MB_SINGLE_FILE = "storage-mb-single-file"
        DURATION_MINUTE_WORKSPACE = "duration-minute-workspace"
        NUMBER_OF_KNOWLEDGE_SOURCES = "number-of-knowledge-sources"
        DURATION_MINUTE_SINGLE_FILE = "duration-minute-single-file"

    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(choices=Code.choices, max_length=100, unique=True)
    products = models.ManyToManyField("api.StripeProduct", through="ProductFeature")
    unit = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    default = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Product Feature"
        verbose_name_plural = "Product Features"
