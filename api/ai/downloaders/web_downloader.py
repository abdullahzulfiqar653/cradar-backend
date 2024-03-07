import time
from typing import Any

import markdown
from django.utils import translation
from html2text import HTML2Text
from html_to_draftjs import html_to_draftjs
from playwright._impl._errors import TimeoutError
from playwright.sync_api import sync_playwright

from api.ai.translator import google_translator


def remove_lines_before_header(markdown_string):
    """
    Detect the header 1 line and remove all the previous lines.
    Return the original markdown_string if no header 1 line is found.
    """
    lines = markdown_string.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("# "):
            return "\n".join(lines[i:])
    return markdown_string


class WebDownloader:
    translator = google_translator

    def download(self, url: str) -> dict[str, Any]:
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch()
                page = browser.new_page()
                page.goto(url, timeout=10000)
                # We wait for 2 seconds for the page to load
                time.sleep(2)
                result = page.content()
            except TimeoutError:
                result = page.content()
        html2text = HTML2Text(baseurl=url)
        html2text.body_width = 0
        html2text.ignore_images = True
        raw_markdown_string = html2text.handle(result)
        markdown_string = remove_lines_before_header(raw_markdown_string)

        # Translate the markdown string
        # We convert \n to <br> before translating and convert it back
        # because google translator doesn't respect the line break character \n
        language = translation.get_language().split("-")[0]
        translated_markdown_string = self.translator.translate(
            markdown_string.replace("\n", "<br>"), language
        ).replace("<br>", "\n")

        html_string = markdown.markdown(translated_markdown_string)
        content_state = html_to_draftjs(html_string)

        return content_state


__all__ = ["WebDownloader"]
