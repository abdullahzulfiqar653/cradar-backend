import stripe
from rest_framework import serializers

from api.stripe import stripe


class StripeCustomerBillingPortalSessionCreateSerializer(serializers.Serializer):
    url = serializers.URLField(
        help_text="Redirect URL to return after Stripe portal session, also used to return the stripe portal URL"
    )

    def create(self, validated_data):
        request = self.context.get("request")
        try:
            session = stripe.billing_portal.Session.create(
                customer=request.workspace.get_stripe_customer_id(request.user),
                return_url=validated_data["url"],
            )
            return {"url": session.url}
        except Exception as e:
            print(e)
            raise serializers.ValidationError(
                "Failed to create Stripe customer billing portal session"
            )
