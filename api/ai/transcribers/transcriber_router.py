from .base_transcriber import BaseTranscriber
from .docx_transcriber import docx_transcriber
from .openai_transcriber import openai_transcriber
from .pdfium_transcriber import pdfium_transcriber
from .text_transcriber import text_transcriber


class TranscriberRouter(BaseTranscriber):
    transcribers: list[BaseTranscriber] = [
        openai_transcriber,
        pdfium_transcriber,
        docx_transcriber,
        text_transcriber,
    ]
    transcriber_used = None

    @property
    def supported_filetypes(self):
        return {
            filetype
            for transcriber in self.transcribers
            for filetype in transcriber.supported_filetypes
        }

    def transcribe(self, filepath: str, filetype: str, language: str) -> str:
        self.check_filetype(filetype)
        for transcriber in self.transcribers:
            if filetype in transcriber.supported_filetypes:
                self.transcriber_used = transcriber
                return transcriber.transcribe(filepath, filetype, language)
