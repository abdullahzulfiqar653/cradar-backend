from rest_framework import exceptions, generics

from api.models.takeaway_type import TakeawayType
from api.serializers.takeaway_type import TakeawayTypeSerializer


class TakeawayTypeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TakeawayType.objects.all()
    serializer_class = TakeawayTypeSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.project.takeaway_types.count() == 1:
            raise exceptions.ValidationError(
                {"detail": "The takeaway type list must not be empty."}
            )
        return super().destroy(request, *args, **kwargs)
