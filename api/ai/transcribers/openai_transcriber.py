import openai

from api.ai.paragrapher import Paragrapher

from .base_transcriber import BaseTranscriber

client = openai.OpenAI()


class OpenAITranscriber(BaseTranscriber):
    paragrapher = Paragrapher()
    supported_filetypes = [
        "flac",
        "mp3",
        "mp4",
        "mpeg",
        "mpga",
        "m4a",
        "ogg",
        "wav",
        "webm",
    ]

    def transcribe(self, filepath, filetype, language):
        self.check_filetype(filetype)
        with open(filepath, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                language=language,
            )
        print("Transcript duration:", transcript.duration)
        segments = (segment["text"] for segment in transcript.segments)
        return self.paragrapher.paragraphing(segments)


openai_transcriber = OpenAITranscriber()
