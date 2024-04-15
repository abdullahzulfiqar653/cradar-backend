from langchain.output_parsers import PydanticOutputParser
from langflow.interface.custom.custom_component import CustomComponent
from pydantic.v1 import BaseModel


class PydanticOutputParserComponent(CustomComponent):
    display_name = "Pydantic Output Parser"
    description = "Pydantic Output Parser"

    def build_config(self):
        return {
            "pydantic_object": {
                "display_name": "Pydantic Object",
                "input_types": ["BaseModel"],
            },
        }

    def build(self, pydantic_object: BaseModel) -> PydanticOutputParser:
        return PydanticOutputParser(pydantic_object=pydantic_object)
