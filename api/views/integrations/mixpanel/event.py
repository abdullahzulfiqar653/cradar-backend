from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from api.serializers.integrations.mixpanel.event import MixpanelEventSerializer


class MixpanelEventCreateView(generics.CreateAPIView):
    serializer_class = MixpanelEventSerializer
    permission_classes = [IsAuthenticated]
