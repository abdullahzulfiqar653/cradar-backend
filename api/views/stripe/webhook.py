from django.conf import settings
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import StripePrice, StripeProduct, StripeSubscription, User
from api.stripe import stripe


class StripeWebhookView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        event = None
        payload = request.body
        sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET_KEY

        def get_date(date):
            return timezone.datetime.fromtimestamp(date)

        # Authenticate stripe request
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Handling events
        match event["type"]:
            case "charge.succeeded":
                pass
            case "payment_method.attached":
                pass
            case "customer.subscription.created":
                # This will be call when we create the subscription automatically
                subscription = event["data"]["object"]
                StripeSubscription.objects.create(
                    user_id=subscription["metadata"]["user_id"],
                    id=subscription["id"],
                    status=subscription["status"],
                    product_id=subscription["plan"]["product"],
                    workspace_id=subscription["metadata"]["workspace_id"],
                    end_at=get_date(subscription["current_period_end"]),
                )
            case "customer.subscription.deleted":
                pass
            case "customer.subscription.resumed":
                pass
            case "customer.subscription.paused":
                pass
            case "customer.subscription.updated":
                # This will be called from billing portal
                subscription = event["data"]["object"]
                StripeSubscription.objects.filter(id=subscription["id"]).update(
                    product_id=subscription["plan"]["product"],
                    # TODO: To figure out how to accurately check if it is free trial
                    is_free_trial=False,
                    end_at=get_date(subscription["current_period_end"]),
                )
                # TODO: will send this to mixpanel
                if subscription["cancel_at_period_end"]:
                    time_of_cancellation = subscription["canceled_at"]
                    will_cancelled_at = subscription["cancel_at"]
                    comment = subscription["cancellation_details"]["comment"]
                    feedback = subscription["cancellation_details"]["feedback"]
                pass
            case "customer.subscription.trial_will_end":
                pass
            case "payment_intent.succeeded":
                pass
            case "payment_intent.created":
                pass
            case "checkout.session.completed":
                # This is called from pricing table
                session = event["data"]["object"]
                user = User.objects.get(username=session.get("customer_email"))
                workspace_id = session.get("client_reference_id")
                subscription = stripe.Subscription.retrieve(session["subscription"])
                product_id = subscription["plan"]["product"]
                StripeSubscription.objects.create(
                    user=user,
                    id=subscription["id"],
                    product_id=product_id,
                    workspace_id=workspace_id,
                    end_at=get_date(subscription["current_period_end"]),
                )
            case "product.created":
                StripeProduct.update_or_create(event["data"]["object"])
            case "product.updated":
                StripeProduct.update_or_create(event["data"]["object"])
            case "product.deleted":
                StripeProduct.objects.filter(id=event["data"]["object"]["id"]).delete()
            case "price.created":
                StripePrice.update_or_create(event["data"]["object"])
            case "price.updated":
                StripePrice.update_or_create(event["data"]["object"])
            case "price.deleted":
                StripePrice.objects.filter(id=event["data"]["object"]["id"]).delete()

        return Response(status=status.HTTP_200_OK)
