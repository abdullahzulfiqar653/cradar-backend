from enum import Enum
from pprint import pprint
from typing import Optional

from langchain import LLMChain, PromptTemplate
from langchain.chains import (
    MapReduceDocumentsChain,
    ReduceDocumentsChain,
    StuffDocumentsChain,
)
from langchain.chains.openai_functions import create_structured_output_chain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.document import Document
from langchain.text_splitter import TokenTextSplitter
from pydantic import BaseModel, Field, constr

from note.models import Note
from tag.models import Keyword

llm = ChatOpenAI()

map_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a skilled professional known for exceptional ability to summarize texts.",
        ),
        (
            "human",
            "Summarize the following text.\n\n{text}",
        ),
    ]
)
map_chain = LLMChain(llm=llm, prompt=map_prompt)


class MeetingType(Enum):
    user_interview = "User Interview"
    discovery_call = "Sales Discovery Call"
    demo_meeting = "Customer Technical Demo Meeting"
    requirement_meeting = "Requirement Gathering Meeting"
    customer_checkin = "Customer Check In"
    business_review = "Quarterly Business Review (QBR)"
    kickoff_meeting = "Customer Kick-off Meeting"
    handoff_meeting = "Customer Hand-off Meeting"


class MetadataSchema(BaseModel):
    title: str = Field(
        description="Title of the meeting. Should be concise but informative."
    )
    description: str = Field(
        description="A short paragraph describing what the meeting is about."
    )
    meeting_type: MeetingType = Field(description="What is the meeting type?")
    summary: list[str] = Field(description="Summary of the text in point form.")
    sentiment: Optional[Note.Sentiment] = Field(
        description="The sentiment of the text."
    )
    keywords: list[constr(max_length=50)] = Field(
        description="The list of relevant keywords of the text."
    )


document_prompt = PromptTemplate(
    input_variables=["page_content"],
    template="{page_content}",
)
document_variable_name = "text"

reduce_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Follow the function parameter schema strictly."),
        ("human", "Extract data from the following summaries.\n\n{text}"),
    ]
)
reduce_chain = create_structured_output_chain(
    MetadataSchema.schema(), llm, reduce_prompt
)

combine_documents_chain = StuffDocumentsChain(
    llm_chain=reduce_chain,
    document_prompt=document_prompt,
    document_variable_name=document_variable_name,
)
reduce_documents_chain = ReduceDocumentsChain(
    combine_documents_chain=combine_documents_chain,
)
map_reduce_chain = MapReduceDocumentsChain(
    llm_chain=map_chain,
    reduce_documents_chain=reduce_documents_chain,
    verbose=True,
)

text_splitter = TokenTextSplitter(
    model_name="gpt-3.5-turbo", chunk_size=1500, chunk_overlap=100
)


def generate_metadata(note: Note):
    doc = Document(page_content=note.content)
    docs = text_splitter.split_documents([doc])

    output = map_reduce_chain.invoke(docs)
    pprint(output)
    metadata = output["output_text"]
    note.title = metadata["title"]
    note.description = metadata["description"]
    note.type = metadata["meeting_type"]
    note.summary = metadata["summary"]
    note.sentiment = metadata.get("sentiment")
    note.save()
    for keyword in metadata["keywords"]:
        keyword, is_created = Keyword.objects.get_or_create(name=keyword)
        note.keywords.add(keyword)
