from google.cloud import translate_v2 as translate
from langdetect import detect


class GoogleTranslator:
    def __init__(self):
        self.client = translate.Client()

    def translate(self, text, language):
        if detect(text) == language:
            return text
        return self.client.translate(text, target_language=language)["translatedText"]


google_translator = GoogleTranslator()
