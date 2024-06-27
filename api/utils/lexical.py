# For type hinting the method with the enclosing class
from __future__ import annotations

import re
from copy import deepcopy
from typing import Callable


def blank_content():
    return {
        "root": {
            "children": [
                {
                    "children": [],
                    "direction": None,
                    "format": "",
                    "indent": 0,
                    "type": "paragraph",
                    "version": 1,
                }
            ],
            "direction": None,
            "format": "",
            "indent": 0,
            "type": "root",
            "version": 1,
        }
    }


class LexicalProcessor:
    def __init__(self, lexical: dict, parent: LexicalProcessor | None = None):
        self.dict = lexical
        self.parent = parent
        self.depth = parent.depth + 1 if parent else 0

    def find_all(self, target: str | Callable[[LexicalProcessor], bool]):
        """
        Traverse a tree of nodes and yield nodes of a specific type.
        @param target: The target type to search for
            or a function that returns True if the node is the target.
        """
        stack = [self]
        if isinstance(target, str):
            target_type = target
            target = lambda node: node.dict["type"] == target_type
        while stack:
            current_node = stack.pop()
            if target(current_node):
                yield current_node
            elif "children" in current_node.dict:
                stack.extend(reversed(current_node.children))

    def flatten(self):
        """
        Traverse a tree of nodes and yield all nodes.
        """
        stack = [self]
        while stack:
            current_node = stack.pop()
            yield current_node
            if "children" in current_node.dict:
                stack.extend(reversed(current_node.children))

    @property
    def children(self):
        return [
            LexicalProcessor(child, parent=self)
            for child in self.dict.get("children", [])
        ]

    def __repr__(self):
        content = self.dict.get("text", "")
        content = self.dict.get("url", "") if not content else content
        if len(content) > 50:
            content = content[:50] + "..."
        content = f" - {content!r}" if content else ""
        indentation = "." * self.depth
        return f"<LexicalProcessor: {indentation}{self.dict['type']}{content}>"

    def to_text(self):
        if self.dict["type"] == "text":
            text = self.dict["text"]
        else:
            text = "".join(node.to_text() for node in self.children)

        match self.dict["type"]:
            case "paragraph" | "heading" | "quote" | "listitem" | "list":
                return text + "\n\n"
            case _:
                return text

    def to_markdown(self):
        # Setting the content
        match self.dict["type"]:
            case "text":
                text = self.dict["text"]
            case "Question":
                text = "<cursor/>\n"
            case "Takeaways":
                from api.models.block import Block

                block = Block.objects.get(id=self.dict["block_id"])
                text = (
                    "Takeaways:\n"
                    + "- "
                    + "\n- ".join(takeaway.title for takeaway in block.takeaways.all())
                    + "\n"
                )
            case "Themes":
                from api.models.block import Block

                block = Block.objects.get(id=self.dict["block_id"])
                text = (
                    "Themes:\n"
                    + "- "
                    + "\n- ".join(theme.title for theme in block.themes.all())
                    + "\n"
                )
            case _:
                text = "".join(node.to_markdown() for node in self.children)

        # Setting the format
        match self.dict["type"]:
            case "paragraph":
                return text + "\n\n"
            case "heading":
                level = re.match(r"^h(\d+)$", self.dict["tag"]).group(1)
                return f'{"#" * int(level)} {text}\n\n'
            case "quote":
                return "> " + text + "\n\n"
            case "link" | "autolink":
                return f'[{text}]({self.dict["url"]})'
            case "listitem":
                return "- " + text + "\n"
            case "list":
                return text + "\n"
            case _:
                return text

    def highlight(self, text: str, id: str):
        if text == "":
            return False

        def compare(str1, str2):
            """
            Compare two strings and return the index and length of the match.
            """
            for i in range(len(str1)):
                compare_len = min(len(str1) - i, len(str2))
                if str1[i : i + compare_len] == str2[:compare_len]:
                    return i, compare_len
            return None, None

        subtext = text
        matches = []
        # Find all nodes to highlight
        for node in self.find_all("text"):
            index, compare_len = compare(node.dict["text"], subtext)
            if index is not None:
                subtext = subtext[compare_len:]
                start = index
                end = index + compare_len
                matches.append((node, start, end))
                if subtext == "":
                    break
            else:
                subtext = text
                matches = []
        if subtext != "":
            return False

        # Highlight the text
        for node, start, end in matches:
            replacing_nodes = []
            if start > 0:
                # Split the text node
                pre_node = deepcopy(node.dict)
                pre_node["text"] = node.dict["text"][:start]
                replacing_nodes.append(pre_node)

            highlighting_node = {
                "ids": [id],
                "type": "mark",
                "format": "",
                "indent": 0,
                "version": 1,
                "children": [
                    deepcopy(node.dict),
                ],
                "direction": "ltr",
            }
            highlighting_node["children"][0]["text"] = node.dict["text"][start:end]
            replacing_nodes.append(highlighting_node)

            if end < len(node.dict["text"]):
                # Split the text node
                post_node = deepcopy(node.dict)
                post_node["text"] = node.dict["text"][end:]
                replacing_nodes.append(post_node)

            i = node.parent.dict["children"].index(node.dict)
            node.parent.dict["children"][i : i + 1] = replacing_nodes
        return True

    def append(self, another: LexicalProcessor):
        another = deepcopy(another)
        self.dict["children"].extend(another.dict["children"])
        return self

    def add_block(self, block):
        self.dict["children"].append(
            {
                "block_id": block.id,
                "type": block.type,
                "version": 1,
            }
        )
        return self
