import json
import re

import markdown
from django.conf import settings
from playwright.sync_api import sync_playwright

from api.ai.translator import GoogleTranslator
from api.utils.lexical import LexicalProcessor


class MarkdownProcessor:
    def __init__(self, markdown):
        self.markdown = markdown

    def set_translator(self, translator: GoogleTranslator):
        self.translator = translator
        return self

    def translate(self, language):
        # Translate the markdown string
        # We convert \n to <br> before translating and convert it back
        # because google translator doesn't respect the line break character \n
        self.markdown = self.translator.translate(
            self.markdown.replace("\n", "<br>"), language
        ).replace("<br>", "\n")
        return self

    def fix_links(self):
        pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)", re.MULTILINE)

        def replace_label(match):
            label = match.group(1).replace("\n", " ").replace("\r", "")
            url = match.group(2)

            # Check if the label starts with one or more '#'
            header_match = re.match(r"^\s*(#+)\s*(.*)", label)
            if header_match:
                header_hashes = header_match.group(1)
                rest_of_label = header_match.group(2).lstrip()
                return f"{header_hashes} [{rest_of_label}]({url})"
            else:
                return f"[{label}]({url})"

        self.markdown = pattern.sub(replace_label, self.markdown)
        return self

    def remove_before_header(self):
        lines = self.markdown.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("# "):
                self.markdown = "\n".join(lines[i:])
                return self
        return self

    def truncate(self):
        lines = []
        length = 0
        for line in self.markdown.split("\n"):
            # The content state json structure for each line is about 120 chars
            length += len(line) + 120
            if length > 220_000:
                lines.append("...[text is truncated because it is too long]")
                break
            lines.append(line)
        self.markdown = "\n".join(lines)
        return self

    def replace_newlines_in_pre_tags(self, text):
        # Define a function to replace newlines with <br> within the <pre></pre> content
        def replace_newlines(match):
            content = match.group(1)  # Extract the content inside <pre></pre>
            return "<pre>{}</pre>".format(content.replace("\n", "<br>"))

        # Use regex to find all <pre></pre> blocks and apply the replacement function
        return re.sub(r"<pre>(.*?)</pre>", replace_newlines, text, flags=re.DOTALL)

    def to_html(self):
        raw_html = markdown.markdown(self.markdown, extensions=["tables"])
        return self.replace_newlines_in_pre_tags(raw_html)

    def to_lexical(self):
        frontend_url = settings.FRONTEND_URL
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.goto(f"{frontend_url}/lexical/html")
            page.locator("#clear-text").click()
            page.locator("#html-input").fill(self.to_html())
            output_str = page.locator("#lexical-json-output").text_content()
            lexical_json = json.loads(output_str)

            # Convert the paragraph format to justify
            lexical = LexicalProcessor(lexical_json["root"])
            lexical.dict["children"] = lexical.dict["children"][1]["children"]
            for paragraph in lexical.find_all("paragraph"):
                paragraph.dict["format"] = "justify"
            return lexical_json
