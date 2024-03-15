import json

from django.utils.translation import gettext
from langchain.output_parsers.openai_functions import PydanticOutputFunctionsParser
from langchain.prompts import ChatPromptTemplate
from langchain.schema.document import Document
from langchain.text_splitter import TokenTextSplitter
from langchain_community.chat_models import ChatOpenAI
from langchain_community.utils.openai_functions import (
    convert_pydantic_to_openai_function,
)
from pydantic.v1 import BaseModel, Field

from api.ai import config
from api.ai.generators.utils import ParserErrorCallbackHandler, token_tracker
from api.ai.translator import google_translator
from api.models.note import Note
from api.models.takeaway import Takeaway
from api.models.takeaway_type import TakeawayType
from api.models.user import User


def get_chain():
    class TakeawaySchema(BaseModel):
        "The takeaway extracted from the text targeted for a specific question."

        topic: str = Field(
            description=gettext("Topic of the takeaway, for grouping the takeaways.")
        )
        title: str = Field(
            description=gettext(
                "What the takeaway is about. "
                "This should be an important message of the text "
                "carrying a single idea."
            )
        )
        significance: str = Field(
            description=gettext("The reason why the takeaway is important.")
        )
        type: str = Field(
            description=gettext(
                "The takeaway type. This is a required field. "
                "For example: 'Pain Point', 'Moment of Delight', "
                "'Pricing', 'Feature Request', 'Moment of Dissatisfaction', "
                "'Usability Issue', or any other issue types deemed logical."
            )
        )

    class TakeawaysSchema(BaseModel):
        "A list of extracted takeaways."

        takeaways: list[TakeawaySchema] = Field(
            description=gettext("A list of takeaways extracted from the text.")
        )

    llm = ChatOpenAI(model=config.model)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                gettext(
                    "Extract the takeaways based on the question from the text. "
                    "Each takeaway must contain 'topic', "
                    "'title', 'significance' and 'type'. "
                    "Extract 5 takeaways for each question."
                ),
            ),
            (
                "human",
                gettext("Question: {question}\n\nText: \n{text}"),
            ),
        ]
    )
    function = convert_pydantic_to_openai_function(TakeawaysSchema)
    function_call = {"name": function["name"]}
    parser = PydanticOutputFunctionsParser(pydantic_schema=TakeawaysSchema)
    chain = (
        prompt
        | llm.bind(
            functions=[function],
            function_call=function_call,
        )
        | parser
    )
    return chain


def generate_takeaways_with_questions(note: Note, created_by: User):
    takeaways_chain = get_chain()

    text_splitter = TokenTextSplitter(
        model_name=config.model,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )

    bot = User.objects.get(username="bot@raijin.ai")
    doc = Document(page_content=note.get_content_text())
    docs = text_splitter.split_documents([doc])

    questions = [
        {"id": question.id, "question": question.title}
        for question in note.questions.all()
    ]
    questions_string = json.dumps(questions)

    with token_tracker(note.project, note, "generate-takeaways", created_by):
        outputs = [
            {
                "question_id": question["id"],
                "output": takeaways_chain.invoke(
                    {"text": doc.page_content, "question": question["question"]},
                    config={"callbacks": [ParserErrorCallbackHandler()]},
                ),
            }
            for question in questions
            for doc in docs
        ]

    generated_takeaways = [
        {
            "title": google_translator.translate(
                f'{takeaway["topic"]} - {takeaway["title"]}: {takeaway["significance"]}',
                note.project.language,
            ),
            "type": takeaway["type"],
            "question_id": output["question_id"],
        }
        for output in outputs
        for takeaway in output["output"].dict()["takeaways"]
    ]

    # Create new takeaway types
    existing_takeaway_types = set(
        TakeawayType.objects.filter(project=note.project).values_list("name", flat=True)
    )
    generated_takeaway_types = {takeaway["type"] for takeaway in generated_takeaways}
    new_takeaway_types = generated_takeaway_types - existing_takeaway_types
    takeaway_types_to_create = []
    for takeaway_type in new_takeaway_types:
        takeaway_types_to_create.append(
            TakeawayType(name=takeaway_type, project=note.project)
        )
    TakeawayType.objects.bulk_create(takeaway_types_to_create)

    # Create takeaways
    takeaway_type_dict = {
        takeaway_type.name: takeaway_type
        for takeaway_type in TakeawayType.objects.filter(project=note.project)
    }
    takeaways_to_add = []
    note_takeaway_sequence = note.takeaway_sequence
    for generated_takeaway in generated_takeaways:
        note_takeaway_sequence += 1
        takeaways_to_add.append(
            Takeaway(
                title=generated_takeaway["title"],
                type=takeaway_type_dict[generated_takeaway["type"]],
                note=note,
                created_by=bot,
                question_id=generated_takeaway["question_id"],
                code=f"{note.code}-{note_takeaway_sequence}",
            )
        )
    Takeaway.objects.bulk_create(takeaways_to_add)
    note.takeaway_sequence = note_takeaway_sequence
    note.save()
