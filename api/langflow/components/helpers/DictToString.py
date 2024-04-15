import json

from langflow.field_typing import Text
from langflow.interface.custom.custom_component import CustomComponent


class DictToStringComponent(CustomComponent):
    display_name = "Dict to String"
    description = "Dict to String"

    def build_config(self):
        return {
            "input": {"display_name": "Input", "input_types": ["dict"]},
            "indent": {
                "display_name": "Indent",
                "field_type": "int",
                "value": 4,
            },
        }

    def build(self, input: dict, indent: int = 4) -> Text:
        return json.dumps(input, indent=indent)
