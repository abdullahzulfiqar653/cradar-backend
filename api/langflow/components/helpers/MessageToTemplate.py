from langflow.field_typing import Text
from langflow.interface.custom.custom_component import CustomComponent


class MessageToTemplateComponent(CustomComponent):
    display_name = "Message to Template"
    description = "Replace single curly bracket with double curly brackets."

    def build_config(self):
        return {
            "input": {
                "display_name": "Input",
                "multiline": True,
            },
        }

    def build(self, input: str) -> Text:
        return input.replace("{", "{{").replace("}", "}}")
