from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from api.ai import config
from api.ai.generators.utils import token_tracker
from api.models.asset import Asset
from api.models.user import User
from api.utils.lexical import LexicalProcessor


def generate_asset_title(asset: Asset, created_by: User):
    system_prompt = (
        "Generate a title for the report below. "
        "The title should be relevant to the content and should be concise. "
        "Do not include quotes."
    )
    content = LexicalProcessor(asset.content["root"]).to_markdown()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", content),
        ]
    )
    llm = ChatOpenAI(model=config.model)
    chain = prompt | llm
    with token_tracker(asset.project, asset, "generate-asset-title", created_by):
        output = chain.invoke({})
    return output.content
