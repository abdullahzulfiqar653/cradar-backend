from textwrap import dedent

from langchain.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI

from api.ai import config
from api.ai.generators.utils import token_tracker
from api.models.note import Note
from api.models.user import User


def generate_message(note: Note, created_by: User):
    # TODO: To handle the case where the prompt exceeds context window
    messages = note.messages.order_by("order")
    system_prompt = dedent(
        """
            Using the following context, generate a message that is relevant to the context and is in a readable format.

            Context:
            {context}
        """
    )
    chat_history = [(message.role, message.text) for message in messages]
    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), *chat_history]
    )
    llm = ChatOpenAI(model=config.model)
    chain = prompt | llm
    query = chat_history[-1][1]
    context = "- " + "\n- ".join(chunk.text for chunk in note.search_chunks(query))
    with token_tracker(note.project, note, "generate-message", created_by):
        output = chain.invoke({"context": context})
    return output.content
