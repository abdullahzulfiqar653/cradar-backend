from django.db import models
from django.utils import timezone
from shortuuid.django_fields import ShortUUIDField


class StripePrice(models.Model):
    id = models.CharField(
        max_length=30,
        primary_key=True,
        editable=False,
        verbose_name="Stripe Price ID"
    )
    product = models.ForeignKey("api.StripeProduct",
                                on_delete=models.CASCADE, editable=False, related_name="product_prices")
    is_active = models.BooleanField()
    nickname = models.CharField(max_length=256, null=True)
    recurring_interval = models.CharField(max_length=30)

    def __str__(self):
        return self.product.name

    @classmethod
    def update_or_create(cls, price_data):
        obj, created = cls.objects.update_or_create(
            id=price_data['id'],
            defaults={
                'product_id': price_data['product'],
                'is_active': price_data['active'],
                'nickname': price_data['nickname'],
                'recurring_interval': price_data['recurring']['interval']
            }
        )
        return obj, created
