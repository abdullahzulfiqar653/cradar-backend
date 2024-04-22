import os
import tempfile
from decimal import Decimal
from time import time
from urllib.parse import urlparse

from django.utils import translation
from pydub.utils import mediainfo

from api.ai.downloaders.web_downloader import WebDownloader
from api.ai.downloaders.youtube_downloader import YoutubeDownloader
from api.ai.generators.metadata_generator import generate_metadata
from api.ai.generators.tag_generator import generate_tags
from api.ai.generators.takeaway_generator_default_question import (
    generate_takeaways_default_question,
)
from api.ai.generators.takeaway_generator_with_questions import (
    generate_takeaways_with_questions,
)
from api.ai.transcribers import openai_transcriber
from api.ai.transcribers.transcriber_router import TranscriberRouter
from api.models.note import Note
from api.models.usage.transciption import TranscriptionUsage
from api.models.user import User
from api.storage_backends import PrivateMediaStorage

youtube_downloader = YoutubeDownloader()
web_downloader = WebDownloader()


class NewNoteAnalyzer:
    transcriber_router = TranscriberRouter()

    def truncate(self, text):
        lines = []
        length = 0
        for line in text.split("\n"):
            # The content state json structure for each line is about 120 chars
            length += len(line) + 120
            if length > 220_000:
                lines.append("...[text is truncated because it is too long]")
                break
            lines.append(line)
        return "\n".join(lines)

    def to_content_state(self, text):
        text = self.truncate(text)
        return {"blocks": [{"text": block} for block in text.split("\n")]}

    def transcribe(self, note, created_by):
        if isinstance(note.file.storage, PrivateMediaStorage):
            self.transcribe_s3_file(note, created_by)
        else:
            self.transcribe_local_file(note, created_by)

    def transcribe_s3_file(self, note, created_by):
        with tempfile.NamedTemporaryFile(suffix=f".{note.file_type}") as temp:
            temp.write(note.file.read())
            temp.seek(0)
            filepath = temp.name
            filetype = os.path.splitext(urlparse(note.file.url).path)[1].strip(".")
            language = note.project.language
            transcript = self.transcriber_router.transcribe(
                filepath, filetype, language
            )

            if transcript is not None:
                note.content = self.to_content_state(transcript)
                note.save()
            self.track_audio_filesize(note, filepath, created_by)

    def transcribe_local_file(self, note, created_by):
        filepath = note.file.path
        filetype = note.file_type
        language = note.project.language
        transcript = self.transcriber_router.transcribe(filepath, filetype, language)
        if transcript is not None:
            note.content = self.to_content_state(transcript)
            note.save()
        self.track_audio_filesize(note, filepath, created_by)

    def track_audio_filesize(self, note: Note, filepath: str, created_by: User):
        if self.transcriber_router.transcriber_used is openai_transcriber:
            audio_info = mediainfo(filepath)
            duration_second = round(float(audio_info["duration"]))
            t = TranscriptionUsage.objects.create(
                workspace=note.project.workspace,
                project=note.project,
                note=note,
                created_by=created_by,
                value=duration_second,
                cost=Decimal("0.0001") * duration_second,
            )

    def download(self, note):
        if youtube_downloader.is_youtube_link(note.url):
            content = youtube_downloader.download(note.url)
            note.content = self.to_content_state(content)
        else:
            note.content = web_downloader.download(note.url)
        note.save()

    def summarize(self, note, created_by):
        print("========>   Generating takeaways")
        if note.questions.count() > 0:
            generate_takeaways_with_questions(note, note.questions.all(), created_by)
        else:
            generate_takeaways_default_question(note, created_by)
        print("========>   Generating metadata")
        generate_metadata(note, created_by)
        print("========>   Generating tags")
        generate_tags(note, created_by)

    def analyze(self, note: Note, created_by: User):
        with translation.override(note.project.language):
            print("========> Start transcribing")
            start = time()
            if note.file:
                self.transcribe(note, created_by)
            elif note.url:
                self.download(note)
            end = time()
            print(f"Elapsed time: {end - start} seconds")
            print("========> Start summarizing")
            self.summarize(note, created_by)
            print("========> End analyzing")


class ExistingNoteAnalyzer(NewNoteAnalyzer):
    def analyze(self, note: Note, created_by: User):
        with translation.override(note.project.language):
            print("========> Start summarizing")
            self.summarize(note, created_by)
            print("========> End analyzing")


class TranscribeOnlyAnalyzer(NewNoteAnalyzer):
    def analyze(self, note: Note, created_by: User):
        with translation.override(note.project.language):
            print("========> Start transcribing")
            start = time()
            if note.file:
                self.transcribe(note, created_by)
            elif note.url:
                self.download(note)
            end = time()
            print(f"Elapsed time: {end - start} seconds")
            print("========> End analyzing")
