import time
from typing import Any

from html2text import HTML2Text
from playwright._impl._errors import TimeoutError
from playwright.sync_api import sync_playwright


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

        return {"markdown": markdown_string}


__all__ = ["WebDownloader"]
