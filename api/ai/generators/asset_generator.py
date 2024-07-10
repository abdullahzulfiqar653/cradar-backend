from textwrap import dedent

from django.db.models import QuerySet
from django.utils.translation import gettext
from langchain.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI

from api.ai import config
from api.ai.generators.utils import token_tracker
from api.models.asset import Asset
from api.models.takeaway import Takeaway
from api.models.user import User
from api.utils.lexical import LexicalProcessor


def construct_prompt(asset: Asset, instruction: str, takeaways: QuerySet[Takeaway]):
    prompt_format = gettext(
        dedent(
            """
                <instruction>{instruction}</instruction>

                <context>
                <content>
                {content}
                </content>

                <notes>
                {notes}
                </notes>
                </context>
            """
        )
    )
    notes = "- " + "\n- ".join([takeaway.title for takeaway in takeaways[:20]])
    content = LexicalProcessor(asset.content["root"]).to_markdown()
    prompt = prompt_format.format(instruction=instruction, content=content, notes=notes)
    return prompt


def generate_content(
    asset: Asset, instruction: str, takeaways: QuerySet[Takeaway], created_by: User
):
    system_prompt = dedent(
        """
            The user is working on a analysis report. 
            Follow the user's instruction to generate the content for the report based on the given context,
            which includes the notes that user has made and the current report content.
            However, if the user's instruction is not related to the context, tell user that the context is irrelevant.
            The tag <cursor/> indicates where the user wants the generated content to be placed.
            The generated content should be relevant to the context and should be in a readable format.
            Keep the generated content to within 300 words.
        """
    )
    human_prompt = construct_prompt(asset, instruction, takeaways)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                gettext(system_prompt),
            ),
            ("human", "{human_prompt}"),
        ]
    )
    llm = ChatOpenAI(model=config.model)
    chain = prompt | llm
    with token_tracker(asset.project, asset, "generate-asset", created_by):
        output = chain.invoke({"human_prompt": human_prompt})
    return output.content
