from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.text import slugify
from shortuuid.django_fields import ShortUUIDField

from api.models.feature import Feature
from api.models.product_feature import ProductFeature
from api.models.stripe_price import StripePrice
from api.models.stripe_subscription import StripeSubscription
from api.models.user import User
from api.models.workspace_user import WorkspaceUser
from api.stripe import stripe


class Workspace(models.Model):
    class UsageType(models.TextChoices):
        PERSONAL = "Personal"
        WORK = "Work"

    class CompanySize(models.TextChoices):
        SIZE_1_10 = "1-10"
        SIZE_11_50 = "11-50"
        SIZE_51_200 = "51-200"
        SIZE_201_500 = "201-500"
        SIZE_501_PLUS = "501+"

    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owned_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="owned_workspaces"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    logo_url = models.URLField(blank=True)
    domain_slug = models.SlugField(max_length=50, unique=True)
    stripe_customer_id = models.CharField(max_length=30, blank=True, editable=False)

    members = models.ManyToManyField(
        User, through=WorkspaceUser, related_name="workspaces"
    )

    usage_type = models.CharField(
        max_length=10, choices=UsageType.choices, editable=False
    )
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(
        choices=CompanySize.choices, max_length=10, blank=True
    )

    @property
    def usage_seconds(self):
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        return (
            self.transcription_usages.filter(created_at__gt=start_of_month)
            .aggregate(value=Coalesce(Sum("value"), 0))
            .get("value")
        )

    @property
    def usage_tokens(self) -> int:
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        return (
            self.token_usages.filter(created_at__gt=start_of_month)
            .aggregate(value=Coalesce(Sum("value"), 0))
            .get("value")
        )

    @property
    def total_file_size(self) -> int:
        return self.notes.aggregate(value=Coalesce(Sum("file_size"), 0)).get("value")

    def __str__(self):
        return f"{self.id} - {self.name}"

    def save(self, *args, **kwargs):
        # Generate the domain slug based on the workspace name
        self.domain_slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_feature_value(self, feature_code):
        feature = Feature.objects.get(code=feature_code)
        product_feature = ProductFeature.objects.filter(
            product__subscriptions__workspace=self,
            product__subscriptions__status__in=[
                StripeSubscription.Status.ACTIVE,
                StripeSubscription.Status.TRIALING,
            ],
            product__subscriptions__end_at__gt=timezone.now(),
            feature=feature,
        ).first()
        return product_feature.value if product_feature else feature.default

    def get_product_price_id(self):
        price = StripePrice.objects.filter(product__usage_type=self.usage_type).first()
        return price.id

    def get_stripe_customer_id(self, user):
        if not self.stripe_customer_id:
            customer = stripe.Customer.create(
                name=user.get_full_name(),
                email=user.username,
                metadata={"user_id": user.id, "workspace_id": self.id},
            )
            self.stripe_customer_id = customer.id
            self.save()
        return self.stripe_customer_id
