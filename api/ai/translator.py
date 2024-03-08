import json
import os

from google.cloud import translate_v2 as translate
from langdetect import detect


class GoogleTranslator:
    def __init__(self):
        google_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if google_credentials is not None:
            self.client = translate.Client.from_service_account_info(
                json.loads(google_credentials)
            )
        else:
            self.client = translate.Client()

    def translate(self, text, language):
        if detect(text) == language:
            return text
        return self.client.translate(text, target_language=language)["translatedText"]


google_translator = GoogleTranslator()
