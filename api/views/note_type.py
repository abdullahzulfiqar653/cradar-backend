from rest_framework import exceptions, generics

from api.models.note_type import NoteType
from api.serializers.note_type import NoteTypeSerializer


class NoteTypeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NoteTypeSerializer
    queryset = NoteType.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.project.note_types.count() == 1:
            raise exceptions.ValidationError(
                {"detail": "The report type list must not be empty."}
            )
        return super().destroy(request, *args, **kwargs)
