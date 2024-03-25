from django.db.models import QuerySet
from django.utils.translation import gettext
from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOpenAI
from tiktoken import encoding_for_model

from api.ai import config
from api.ai.generators.utils import token_tracker
from api.models.block import Block
from api.models.takeaway import Takeaway
from api.models.user import User


def construct_prompt(question: str, takeaways: QuerySet[Takeaway]):
    encoder = encoding_for_model(config.model)
    prompt_format = gettext("Question: {question}\n\nContext:\n")
    prompt = prompt_format.format(question=question)
    current_token_count = len(encoder.encode(prompt))
    for takeaway in takeaways:
        takeaway_token_count = len(encoder.encode(takeaway.title))
        if current_token_count + takeaway_token_count + 2 > config.chunk_size:
            return prompt
        prompt += "- " + takeaway.title + "\n"
        current_token_count += takeaway_token_count + 2
    return prompt


def generate_block(
    block: Block, question: str, takeaways: QuerySet[Takeaway], created_by: User
):
    human_prompt = construct_prompt(question, takeaways)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                gettext("Answer the following question based on the given context."),
            ),
            ("human", human_prompt),
        ]
    )
    llm = ChatOpenAI(model=config.model)
    chain = prompt | llm
    with token_tracker(block.asset.project, block, "generate-block", created_by):
        output = chain.invoke({})
    block.content = {"markdown": output.content}
    block.save()
