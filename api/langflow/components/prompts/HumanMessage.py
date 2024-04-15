from langchain_core.messages import HumanMessage
from langchain_core.prompts import HumanMessagePromptTemplate
from langflow.field_typing import Prompt, Text
from langflow.interface.custom.custom_component import CustomComponent
from langflow.template.field.base import TemplateField


class HumanMessageComponent(CustomComponent):
    display_name: str = "Human Message Prompt Template"
    description: str = "Create a human prompt template with dynamic variables."
    icon = "prompts"

    def build_config(self):
        return {
            "template": TemplateField(display_name="Template"),
            "code": TemplateField(advanced=True),
        }

    def build(
        self,
        template: Prompt,
        **kwargs,
    ) -> HumanMessage:
        from langflow.base.prompts.utils import dict_values_to_string

        prompt_template = HumanMessagePromptTemplate.from_template(Text(template))
        kwargs = dict_values_to_string(kwargs)
        kwargs = {
            k: "\n".join(v) if isinstance(v, list) else v for k, v in kwargs.items()
        }
        try:
            formated_prompt = prompt_template.format(**kwargs)
        except Exception as exc:
            raise ValueError(f"Error formatting prompt: {exc}") from exc
        self.status = f'Prompt:\n"{formated_prompt}"'
        return formated_prompt
