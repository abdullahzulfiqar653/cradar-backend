from rest_framework import generics

from api.models.takeaway_type import TakeawayType
from api.serializers.takeaway_type import TakeawayTypeSerializer


class TakeawayTypeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TakeawayType.objects.all()
    serializer_class = TakeawayTypeSerializer
