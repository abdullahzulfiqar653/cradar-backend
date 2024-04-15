from langflow.interface.custom.custom_component import CustomComponent
from pydantic.v1 import BaseModel, Field


class TakeawaysPydanticComponent(CustomComponent):
    display_name = "Takeaways Pydantic"
    description = "Takeaways pydantic model for extracting takeaways from text."

    def build_config(self):
        return {}

    def build(self) -> BaseModel:

        class TakeawayPydantic(BaseModel):
            "The takeaway extracted from the text targeted for a specific question."

            topic: str = Field(
                description=("Topic of the takeaway, for grouping the takeaways.")
            )
            title: str = Field(
                description=(
                    "What the takeaway is about. "
                    "This should be an important message of the text "
                    "carrying a single idea."
                )
            )
            significance: str = Field(
                description=("The reason why the takeaway is important.")
            )
            type: str = Field(
                description=(
                    "The takeaway type. For example: 'Pain Point', 'Moment of Delight', "
                    "'Pricing', 'Feature Request', 'Moment of Dissatisfaction', "
                    "'Usability Issue', or any other issue types deemed logical."
                )
            )

        class TakeawaysPydantic(BaseModel):
            "A list of extracted takeaways."

            takeaways: list[TakeawayPydantic] = Field(
                description=("A list of takeaways extracted from the text.")
            )

        return TakeawaysPydantic
