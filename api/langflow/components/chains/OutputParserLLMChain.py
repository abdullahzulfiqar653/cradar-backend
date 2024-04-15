from typing import Optional

from langchain.chains.llm import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import BaseLLMOutputParser
from langflow.field_typing import BaseLanguageModel, BaseMemory, Text
from langflow.interface.custom.custom_component import CustomComponent


class CustomLLMChainComponent(CustomComponent):
    display_name = "Custom LLMChain"
    description = "Chain to run queries against LLMs"

    def build_config(self):
        return {
            "prompt": {"display_name": "Prompt", "input_types": ["ChatPromptTemplate"]},
            "llm": {"display_name": "LLM"},
            "memory": {"display_name": "Memory"},
            "output_parser": {"display_name": "Output Parser", "required": False},
        }

    def build(
        self,
        prompt: ChatPromptTemplate,
        llm: BaseLanguageModel,
        memory: Optional[BaseMemory] = None,
        output_parser: Optional[BaseLLMOutputParser] = None,
    ) -> Text:
        if output_parser is not None:
            runnable = LLMChain(
                prompt=prompt, llm=llm, memory=memory, output_parser=output_parser
            )
        else:
            runnable = LLMChain(prompt=prompt, llm=llm, memory=memory)
        result_dict = runnable.invoke({})
        output_key = runnable.output_key
        result = result_dict[output_key]
        self.status = result
        return result
