from langflow.interface.custom.custom_component import CustomComponent
from pydantic.v1 import BaseModel


class PydanticParserComponent(CustomComponent):
    display_name = "Pydantic Parser"
    description = "Pydantic Parser"

    def build_config(self):
        return {
            "input": {"display_name": "Input"},
            "pydantic_object": {
                "display_name": "Pydantic Object",
                "input_types": ["BaseModel"],
            },
        }

    def build(self, input: str, pydantic_object: BaseModel) -> dict:
        return pydantic_object.parse_raw(input).dict()
