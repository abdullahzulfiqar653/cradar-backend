import json

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Count
from django.http.request import QueryDict
from pydub.utils import mediainfo
from rest_framework import exceptions, generics, serializers

from api.ai.transcribers import openai_transcriber
from api.filters.note import NoteFilter
from api.models.note import Note
from api.serializers.note import ProjectNoteSerializer
from api.tasks import analyze_new_note


class ProjectNoteListCreateView(generics.ListCreateAPIView):
    queryset = Note.objects.all()
    serializer_class = ProjectNoteSerializer
    filterset_class = NoteFilter
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
        return self.request.project.notes.annotate(
            takeaway_count=Count("takeaways"),
        )

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
        if serializer.validated_data["file"] is None:
            # Skip checking if no file uploaded
            return

        file = serializer.validated_data["file"].file
        file_type = file.name.split(".")[-1]
        if file_type not in openai_transcriber.supported_filetypes:
            # Skip checking for transcription limit if not audio file
            return

        file_size = serializer.validated_data["file"].size
        total_file_size_in_gb = file_size / 1024 / 1024 / 1024
        if total_file_size_in_gb > settings.STORAGE_GB_WORKSPACE:
            limit = settings.STORAGE_GB_WORKSPACE
            raise exceptions.PermissionDenied(
                f"You have reached the storage limit of {limit} GB."
            )

        # Extract audio info
        audio_info = mediainfo(file.name)
        if audio_info.get("duration") is None:
            raise exceptions.ValidationError("Failed to get audio file information.")

        # Check current audio file limit
        audio_duration_in_seconds = float(audio_info.get("duration"))
        audio_duration_in_minutes = audio_duration_in_seconds / 60
        if audio_duration_in_minutes > settings.DURATION_MINUTE_SINGLE_FILE:
            limit = settings.DURATION_MINUTE_SINGLE_FILE
            raise exceptions.PermissionDenied(
                f"Please only upload audio file with less than {limit} minutes. "
                f"The current file has duration {round(audio_duration_in_minutes)} minutes."
            )

        # Check workspace-wise audio file limit
        workspace = self.request.project.workspace
        total_seconds = workspace.usage_seconds + audio_duration_in_seconds
        total_minutes = total_seconds / 60
        if total_minutes > settings.DURATION_MINUTE_WORKSPACE:
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
            analyze_new_note.delay(note.id, self.request.user.id)
