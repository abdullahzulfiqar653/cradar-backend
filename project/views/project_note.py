import json
from threading import Thread
from time import time

from django.core.files.uploadedfile import UploadedFile
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce, Round
from django.http.request import QueryDict
from django.shortcuts import get_object_or_404
from langchain.callbacks import get_openai_callback
from pydub.utils import mediainfo
from rest_framework import exceptions, generics, serializers

from note.filters import NoteFilter
from note.models import Note
from note.serializers import ProjectNoteSerializer
from project.generators.metadata_generator import generate_metadata
from project.generators.takeaway_generator import generate_takeaways
from project.models import Project
from transcriber.transcribers import omni_transcriber, openai_transcriber
from workspace.models import Workspace

transcriber = omni_transcriber


class ProjectNoteListCreateView(generics.ListCreateAPIView):
    queryset = Note.objects.all()
    serializer_class = ProjectNoteSerializer
    filterset_class = NoteFilter
    ordering_fields = [
        "created_at",
        "takeaway_count",
        "author__first_name",
        "author__last_name",
        "company_name",
        "title",
    ]
    search_fields = [
        "title",
        "author__username",
        "author__first_name",
        "author__last_name",
        "company_name",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        project_id = self.kwargs["project_id"]
        project = get_object_or_404(Project, id=project_id)
        if not project.users.contains(self.request.user):
            raise exceptions.PermissionDenied
        return project.notes.annotate(
            takeaway_count=Count("takeaways"),
            participant_count=Count("user_participants"),
        )

    def get_project(self):
        project_id = self.kwargs.get("project_id")
        project = get_object_or_404(Project, id=project_id)
        if not project.users.contains(self.request.user):
            raise exceptions.PermissionDenied
        return project

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

        return super().get_serializer(*args, **kwargs)

    def check_eligibility(self, project: Project):
        workspace = (
            Workspace.objects.filter(id=project.workspace.id)
            .annotate(
                usage_minutes=Coalesce(
                    Round(Sum("projects__notes__file_duration_seconds") / 60),
                    0,
                )
            )
            .annotate(
                usage_tokens=Coalesce(Sum("projects__notes__analyzing_tokens"), 0)
            )
            .first()
        )
        if (workspace.usage_minutes > 60) or (workspace.usage_tokens > 50_000):
            raise exceptions.PermissionDenied("Quota limit is hit.")

    def perform_create(self, serializer):
        project = self.get_project()
        # self.check_eligibility(project)
        note = serializer.save(author=self.request.user, project=project)
        if note.file:
            thread = Thread(
                target=self.analyze,
                kwargs={"note": note},
            )
            thread.start()

    def update_audio_filesize(self, note):
        if (
            openai_transcriber in transcriber.transcribers
            and note.file_type in openai_transcriber.supported_filetypes
        ):
            audio_info = mediainfo(note.file.path)
            note.file_duration_seconds = round(float(audio_info["duration"]))
            note.analyzing_cost += note.file_duration_seconds / 60 * 0.006
            note.save()

    def transcribe(self, note):
        filepath = note.file.path
        filetype = note.file_type
        language = note.project.language
        transcript = transcriber.transcribe(filepath, filetype, language)
        if transcript is not None:
            note.content = transcript
            note.save()

    def summarize(self, note):
        with get_openai_callback() as callback:
            generate_takeaways(note)
            generate_metadata(note)
            note.analyzing_tokens += callback.total_tokens
            note.analyzing_cost += callback.total_cost
        note.save()

    def analyze(self, note):
        note.is_analyzing = True
        note.save()
        try:
            print("========> Start transcribing")
            start = time()
            self.transcribe(note)
            self.update_audio_filesize(note)
            end = time()
            print(f"Elapsed time: {end - start} seconds")
            print("========> Start summarizing")
            self.summarize(note)
            print("========> End analyzing")
        except Exception as e:
            import traceback

            traceback.print_exc()
        note.is_analyzing = False
        note.save()
