import json

from langflow.field_typing import Text
from langflow.interface.custom.custom_component import CustomComponent


class FormatJsonComponent(CustomComponent):
    display_name = "Format JSON"
    description = "Format JSON string."

    def build_config(self):
        return {
            "input": {
                "display_name": "Input",
                "multiline": True,
            },
            "indent": {
                "display_name": "Indent",
                "field_type": "int",
                "value": 4,
            },
        }

    def build(self, input: str, indent: int = 4) -> Text:
        return json.dumps(json.loads(input), indent=indent)
