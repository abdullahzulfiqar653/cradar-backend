from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langflow.interface.custom.custom_component import CustomComponent
from langflow.template.field.base import TemplateField


class HumanMessageComponent(CustomComponent):
    display_name: str = "Chat Prompt Template"
    description: str = "Prompt template for chat models."
    icon = "prompts"

    def build_config(self):
        return {
            "messages": {
                "display_name": "Messages",
                "input_types": ["HumanMessage", "SystemMessage"],
                "is_list": True,
            },
            "code": TemplateField(advanced=True),
        }

    def build(
        self,
        messages: list[BaseMessage],
    ) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(messages)
