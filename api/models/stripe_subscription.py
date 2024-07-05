from django.db import models


class StripeSubscription(models.Model):
    class Status(models.TextChoices):
        # Ref: The complete list is in https://docs.stripe.com/api/subscriptions/object#subscription_object-status
        INCOMPLETE = "incomplete"
        INCOMPLETE_EXPIRED = "incomplete_expired"
        TRIALING = "trialing"
        ACTIVE = "active"
        PAST_DUE = "past_due"
        CANCELED = "canceled"
        UNPAID = "unpaid"
        PAUSED = "paused"

    id = models.CharField(
        max_length=30,
        primary_key=True,
        editable=False,
        verbose_name="Stripe Subscription ID",
    )
    end_at = models.DateTimeField()  # this comes from Stripe
    status = models.CharField(max_length=20, choices=Status.choices)
    started_at = models.DateTimeField(auto_now_add=True)
    is_free_trial = models.BooleanField(default=True)
    user = models.ForeignKey("api.User", on_delete=models.CASCADE)
    product = models.ForeignKey(
        "api.StripeProduct",
        on_delete=models.SET_NULL,
        null=True,
        related_name="subscriptions",
    )
    workspace = models.OneToOneField(
        "api.Workspace",
        on_delete=models.SET_NULL,
        null=True,
        related_name="subscription",
    )

    def __str__(self):
        return f"{self.workspace} - {self.product.name} ({self.user.username})"

    class Meta:
        verbose_name = "Stripe Subscription"
        verbose_name_plural = "Stripe Subscriptions"
