from pprint import pprint

from django.contrib.auth.models import User as AuthUser
from langchain.chains.openai_functions import create_structured_output_chain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.document import Document
from langchain.text_splitter import TokenTextSplitter
from pydantic import BaseModel, Field

from note.models import Note
from takeaway.models import Takeaway


class TakeawaySchema(BaseModel):
    topic: str = Field(description="Topic of the takeaway, for grouping the takeaways.")
    title: str = Field(
        description="What the takeaway is about. This should be an important message, issue, learning point or pain point of the text."
    )
    significance: str = Field(description="The reason why the takeaway is important.")


class TakeawaysSchema(BaseModel):
    takeaways: list[TakeawaySchema] = Field(
        description="A list of ten to twenty important takeaways of the text.",
        min_items=10,
        max_items=20,
    )


llm = ChatOpenAI()
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an experienced product analyst. You are experienced in identifying pain points and takeaways from user interviews.",
        ),
        (
            "human",
            "Identify Important Takeaways/Issues/Learning Points in the below given text and reasons why they are important.\n\n{text}",
        ),
    ]
)
takeaways_chain = create_structured_output_chain(
    TakeawaysSchema.schema(), llm, prompt, verbose=True
)

text_splitter = TokenTextSplitter(
    model_name="gpt-3.5-turbo", chunk_size=1500, chunk_overlap=100
)


def generate_takeaways(note: Note):
    bot = AuthUser.objects.get(username="bot@raijin.ai")
    doc = Document(page_content=note.content)
    docs = text_splitter.split_documents([doc])
    outputs = [takeaways_chain.invoke(doc.page_content) for doc in docs]
    pprint(outputs)
    output_takeaways = [
        f'{takeaway["topic"]} - {takeaway["title"]}: {takeaway["significance"]}'
        for output in outputs
        for takeaway in output["function"]["takeaways"]
    ]
    for takeaway_title in output_takeaways:
        takeaway = Takeaway(title=takeaway_title, note=note, created_by=bot)
        takeaway.save()
