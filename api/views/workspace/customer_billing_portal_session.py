from rest_framework import generics

from api.permissions import IsWorkspaceOwner
from api.serializers.customer_billing_portal_session import (
    StripeCustomerBillingPortalSessionCreateSerializer,
)


class StripeBillingPortalSessionCreateView(generics.CreateAPIView):
    serializer_class = StripeCustomerBillingPortalSessionCreateSerializer
    permission_classes = [IsWorkspaceOwner]
