import json

from django.db.models import QuerySet
from django.utils.translation import gettext
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.schema.document import Document
from langchain.text_splitter import TokenTextSplitter
from langchain_community.chat_models import ChatOpenAI
from pydantic.v1 import BaseModel, Field

from api.ai import config
from api.ai.generators.utils import ParserErrorCallbackHandler, token_tracker
from api.ai.translator import google_translator
from api.models.note import Note
from api.models.question import Question
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
                "The takeaway type. For example: 'Pain Point', 'Moment of Delight', "
                "'Pricing', 'Feature Request', 'Moment of Dissatisfaction', "
                "'Usability Issue', or any other issue types deemed logical."
            )
        )

    class TakeawaysSchema(BaseModel):
        "A list of extracted takeaways."

        takeaways: list[TakeawaySchema] = Field(
            description=gettext("A list of takeaways extracted from the text.")
        )

    schema = TakeawaysSchema.schema_json().replace("{", "{{").replace("}", "}}")
    example = (
        json.dumps(
            {
                "takeaways": [
                    {
                        "topic": "Takeaway topic",
                        "title": "What the takeaway is about.",
                        "significance": "The reason why the takeaway is important.",
                        "type": "One word summary of the takeaway topic",
                    }
                ]
            }
        )
        .replace("{", "{{")
        .replace("}", "}}")
    )

    llm = ChatOpenAI(model=config.model)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                gettext(
                    "Extract takeaways from the text based on the question below.\n"
                    "Separate different ideas into each takeaway, "
                    "each takeaway should convey a single idea only.\n"
                    "Each takeaway should contain a topic, a title, "
                    "the significance of the takeaway, and the takeaway type.\n"
                    "Generate JSON data according to the following schema:\n\n"
                    "Schema:\n"
                    f"{schema}\n\n"
                    "For example, the output should be the following:\n"
                    f"{example}\n\n"
                    "Question:\n"
                    "{question}\n\n"
                ),
            ),
            (
                "human",
                gettext("\nText: \n{text}"),
            ),
        ]
    )
    parser = PydanticOutputParser(pydantic_object=TakeawaysSchema)
    chain = prompt | llm.bind(response_format={"type": "json_object"}) | parser
    return chain


def generate_takeaways_with_questions(
    note: Note, questions: QuerySet[Question], created_by: User
):
    takeaways_chain = get_chain()

    text_splitter = TokenTextSplitter(
        model_name=config.model,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )

    bot = User.objects.get(username="bot@raijin.ai")
    doc = Document(page_content=note.get_content_text())
    docs = text_splitter.split_documents([doc])

    with token_tracker(note.project, note, "generate-takeaways", created_by):
        outputs = [
            {
                "question_id": question.id,
                "output": takeaways_chain.invoke(
                    {"text": doc.page_content, "question": question.title},
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
            "type": google_translator.translate(
                takeaway["type"],
                note.project.language,
            ),
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
