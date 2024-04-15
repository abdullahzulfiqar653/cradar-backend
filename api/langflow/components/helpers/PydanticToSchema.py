from langflow.field_typing import Text
from langflow.interface.custom.custom_component import CustomComponent
from pydantic.v1 import BaseModel


class PydanticToSchemaComponent(CustomComponent):
    display_name = "Pydantic to Schema"
    description = "Convert Pydantic object to JSON schema string."

    def build_config(self):
        return {
            "pydantic_object": {
                "display_name": "Pydantic Object",
                "input_types": ["BaseModel"],
            },
            "indent": {
                "display_name": "Indent",
                "field_type": "int",
                "value": 4,
            },
        }

    def build(self, pydantic_object: BaseModel, indent: int = 4) -> Text:
        return pydantic_object.schema_json(indent=indent)
