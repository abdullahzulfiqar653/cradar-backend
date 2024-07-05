import json

from django.core.files.uploadedfile import UploadedFile
from django.http.request import QueryDict
from django_filters.rest_framework import DjangoFilterBackend
from pydub.utils import mediainfo
from rest_framework import exceptions, filters, generics, serializers
from rest_framework.filters import BaseFilterBackend

from api.ai.transcribers import openai_transcriber
from api.filters.note import NoteFilter
from api.models.feature import Feature
from api.models.note import Note
from api.models.property import Property
from api.serializers.note import ProjectNoteSerializer
from api.tasks import analyze_new_note


class PropertyFilter(BaseFilterBackend):
    # Applicable only to Note queryset
    def filter_queryset(self, request, queryset, view):
        for key in request.query_params.keys():
            if not key.startswith("property_"):
                continue
            property_id = key[len("property_") :][:12]
            # operator = key[len("property_") :][12:]
            property = request.project.properties.filter(id=property_id).first()
            if property is None:
                continue
            values = request.query_params.getlist(key)
            match property.data_type:
                case Property.DataType.TEXT:
                    queryset = queryset.filter(
                        note_properties__property=property,
                        note_properties__text_value__in=values,
                    )
                case Property.DataType.NUMBER:
                    queryset = queryset.filter(
                        note_properties__property=property,
                        note_properties__number_value__in=values,
                    )
                case Property.DataType.SELECT:
                    queryset = queryset.filter(
                        note_properties__property=property,
                        note_properties__options__name__in=values,
                        note_properties__notepropertyoption__order=0,
                    )
                case Property.DataType.MULTISELECT:
                    queryset = queryset.filter(
                        note_properties__property=property,
                        note_properties__options__name__in=values,
                    )
        return queryset


class ProjectNoteListCreateView(generics.ListCreateAPIView):
    queryset = Note.objects.all()
    serializer_class = ProjectNoteSerializer
    filterset_class = NoteFilter
    filter_backends = [
        DjangoFilterBackend,
        PropertyFilter,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    ordering_fields = [
        "created_at",
        "takeaway_count",
        "author__first_name",
        "author__last_name",
        "organizations__name",
        "title",
    ]
    search_fields = [
        "title",
        "author__username",
        "author__first_name",
        "author__last_name",
        "organizations__name",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        return ProjectNoteSerializer.optimize_query(self.request.project.notes.all())

    def to_dict(self, form_data):
        data_file = form_data.get("data")
        if not isinstance(data_file, UploadedFile):
            raise serializers.ValidationError("`data` field must be a blob.")
        data = json.load(data_file)
        data["file"] = form_data.get("file")
        return data

    def get_serializer(self, *args, **kwargs):
        # Convert data to json if the request is multipart form
        data = kwargs.get("data")

        if data is None:
            # If it is not POST request, data is None
            return super().get_serializer(*args, **kwargs)

        if isinstance(data, QueryDict):
            kwargs["data"] = self.to_dict(data)
            data = kwargs["data"]

        # In multipart form, null will be treated as string instead of converting to None
        # We need to manually handle the null
        if "revenue" not in data or data["revenue"] == "null":
            data["revenue"] = None

        if "file" not in data or data["file"] == "null":
            data["file"] = None

        if "url" in data and "://" not in data["url"]:
            # Django URLValidator returns invalid if no schema
            # so we manually add in the schema if not provided
            data["url"] = "http://" + data["url"]

        return super().get_serializer(*args, **kwargs)

    def check_eligibility(self, serializer):
        workspace = self.request.project.workspace

        if serializer.validated_data["file"] is None:
            # Skip checking if no file uploaded
            return

        file = serializer.validated_data["file"].file
        file_type = file.name.split(".")[-1]
        if file_type not in openai_transcriber.supported_filetypes:
            # Skip checking for transcription limit if not audio file
            return

        notes_limit = workspace.get_feature_value(
            Feature.Code.NUMBER_OF_KNOWLEDGE_SOURCES
        )
        if workspace.notes.count() >= notes_limit:
            raise exceptions.PermissionDenied(
                f"You have reached the limit of {notes_limit} Knowledge sources."
            )

        file_size_in_bytes = serializer.validated_data["file"].size
        file_size_in_mb = file_size_in_bytes / 1024 / 1024
        mb_limit = workspace.get_feature_value(Feature.Code.STORAGE_MB_SINGLE_FILE)
        if file_size_in_mb > mb_limit:
            raise exceptions.PermissionDenied(
                f"You have reached the storage limit of {mb_limit} MB."
            )

        gb_limit = workspace.get_feature_value(Feature.Code.STORAGE_GB_WORKSPACE)
        total_bytes = workspace.total_file_size + file_size_in_bytes
        total_gbs = total_bytes / 1024 / 1024 / 1024
        if total_gbs > gb_limit:
            raise exceptions.PermissionDenied(
                f"You have reached the storage limit of {gb_limit} GB."
            )

        # Extract audio info
        audio_info = mediainfo(file.name)
        if audio_info.get("duration") is None:
            raise exceptions.ValidationError("Failed to get audio file information.")

        # Check current audio file limit
        audio_duration_in_seconds = float(audio_info.get("duration"))
        audio_duration_in_minutes = audio_duration_in_seconds / 60
        minutes_limit = workspace.get_feature_value(
            Feature.Code.DURATION_MINUTE_SINGLE_FILE
        )
        if audio_duration_in_minutes > minutes_limit:
            raise exceptions.PermissionDenied(
                f"Please only upload audio file with less than {minutes_limit} minutes. "
                f"The current file has duration {round(audio_duration_in_minutes)} minutes."
            )

        # Check workspace-wise audio file limit
        minutes_limit = workspace.get_feature_value(
            Feature.Code.DURATION_MINUTE_WORKSPACE
        )
        total_seconds = workspace.usage_seconds + audio_duration_in_seconds
        total_minutes = total_seconds / 60
        if total_minutes > minutes_limit:
            raise exceptions.PermissionDenied(
                "You have reached the audio transcription limit "
                "so you can no longer upload audio files this month. "
                "Your limit will reset in the next month. "
                "Please contact our Support if you still need more assistance."
            )

    def perform_create(self, serializer):
        self.check_eligibility(serializer)
        note = serializer.save(author=self.request.user, project=self.request.project)
        if note.file or note.url:
            analyze_new_note.delay_on_commit(note.id, self.request.user.id)
