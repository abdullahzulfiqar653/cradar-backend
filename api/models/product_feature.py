from django.db import models
from shortuuid.django_fields import ShortUUIDField


class ProductFeature(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    product = models.ForeignKey(
        "api.StripeProduct", on_delete=models.CASCADE, related_name="product_features"
    )
    feature = models.ForeignKey(
        "api.Feature", on_delete=models.CASCADE, related_name="product_features"
    )
    value = models.PositiveIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.value:
            self.value = None
        super(ProductFeature, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.feature.name}: {self.value}"

    class Meta:
        verbose_name = "Product Feature Assignment"
        verbose_name_plural = "Product Feature Assignments"
        unique_together = ("product", "feature")
