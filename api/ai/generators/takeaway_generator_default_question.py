import json

import numpy as np
from django.db import transaction
from django.db.models import QuerySet
from django.utils.translation import gettext
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.schema.document import Document
from langchain.text_splitter import TokenTextSplitter
from langchain_openai.chat_models import ChatOpenAI
from nltk.tokenize import sent_tokenize
from pgvector.django import MaxInnerProduct
from pydantic.v1 import BaseModel, Field

from api.ai import config
from api.ai.embedder import embedder
from api.ai.generators.utils import ParserErrorCallbackHandler, token_tracker
from api.ai.translator import google_translator
from api.models.highlight import Highlight
from api.models.note import Note
from api.models.takeaway import Takeaway
from api.models.takeaway_type import TakeawayType
from api.models.user import User
from api.utils.lexical import LexicalProcessor

system_prompt = """Extract takeaways from the text below.

Separate different ideas into each takeaway,
each takeaway should convey a single idea only.

Each takeaway should contain a topic, an insight,
the significance of the takeaway, and the takeaway type.

Give your output solely from information extracted from user given text.

Generate JSON data according to the following schema:


Schema:

{schema}


For example, the output should be the following:

{example}"""


def get_chain():
    class TakeawaySchema(BaseModel):
        "The takeaway extracted from the text."

        topic: str = Field(
            description=gettext("Topic of the takeaway, for grouping the takeaways.")
        )
        insight: str = Field(
            description=gettext(
                "What the takeaway is about. "
                "This should be an important insight of the text "
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

    schema = TakeawaysSchema.schema_json(indent=4).replace("{", "{{").replace("}", "}}")
    example = (
        json.dumps(
            {
                "takeaways": [
                    {
                        "topic": "Poor Onboarding Experience",
                        "insight": "This user complains that the onboarding and setup experience is terrible and does not know how to get to the core value of the software",
                        "significance": "[The significance of the takeaway]",
                        "type": "Pain Point",
                    },
                    {
                        "topic": "Automated User Research and Automated Tagging",
                        "insight": "This user was delighted that the software automated away all of their manual tasks for user research when it automatically tagged all the notes that the user created",
                        "significance": "[The significance of the takeaway]",
                        "type": "Moment of Delight",
                    },
                    {
                        "topic": "Not doing enough user interviews",
                        "insight": "[User's name] mentioned that they would like to be able to do more interviews on their customer brands and investigate what are their problems. This would then allow them to identify problem statements that they can solve for their customer brands",
                        "significance": "[The significance of the takeaway]",
                        "type": "Pain Point",
                    },
                ]
            },
            indent=4,
        )
        .replace("{", "{{")
        .replace("}", "}}")
    )

    llm = ChatOpenAI(model=config.model)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                gettext(system_prompt.format(schema=schema, example=example)),
            ),
            (
                "human",
                "\n\n{text}",
            ),
        ]
    )
    parser = PydanticOutputParser(pydantic_object=TakeawaysSchema)
    chain = prompt | llm.bind(response_format={"type": "json_object"}) | parser
    return chain


def generate_takeaways_default_question(note: Note, created_by: User):
    takeaways_chain = get_chain()

    text_splitter = TokenTextSplitter(
        model_name=config.model,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )

    bot = User.objects.get(username="bot@raijin.ai")
    doc = Document(page_content=note.get_content_markdown())
    docs = text_splitter.split_documents([doc])
    with token_tracker(note.project, note, "generate-takeaways", created_by):
        outputs = [
            takeaways_chain.invoke(
                {"text": doc.page_content},
                config={"callbacks": [ParserErrorCallbackHandler()]},
            )
            for doc in docs
        ]

    # Post processing the LLM response
    generated_takeaways = [
        {
            "title": google_translator.translate(
                f'{takeaway["topic"]} - {takeaway["insight"].rstrip(".")}: {takeaway["significance"]}',
                note.project.language,
            ),
            "type": google_translator.translate(
                takeaway["type"],
                note.project.language,
            ),
        }
        for output in outputs
        for takeaway in output.dict()["takeaways"]
    ]

    # Embed note content
    lexical = LexicalProcessor(note.content["root"])
    sentences = [
        sentence
        for paragraph in lexical.to_text().split("\n")
        for sentence in sent_tokenize(paragraph)
        if sentence.strip()  # Check if there is some text after stripping
    ]
    doc_vecs = np.array(embedder.embed_documents(sentences))

    # Create takeaways
    takeaway_type_dict = {
        takeaway_type.name: takeaway_type
        for takeaway_type in TakeawayType.objects.filter(project=note.project)
    }
    generated_takeaway_titles = [takeaway["title"] for takeaway in generated_takeaways]
    generated_takeaway_vectors = embedder.embed_documents(generated_takeaway_titles)
    note_takeaway_sequence = note.takeaway_sequence
    takeaways_to_create = []
    highlights_to_create = []
    for generated_takeaway, vector in zip(
        generated_takeaways, generated_takeaway_vectors
    ):
        note_takeaway_sequence += 1
        # Map takeaway type
        if generated_takeaway["type"] in takeaway_type_dict:
            takeaway_type = takeaway_type_dict[generated_takeaway["type"]]
        else:
            query_vector = embedder.embed_query(generated_takeaway["type"])
            takeaway_type = (
                TakeawayType.objects.filter(project=note.project)
                .order_by(MaxInnerProduct("vector", query_vector))
                .first()
            )
        takeaway = Takeaway(
            title=generated_takeaway["title"],
            vector=vector,
            type=takeaway_type,
            note=note,
            created_by=bot,
            code=f"{note.code}-{note_takeaway_sequence}",
        )

        scores = np.array(vector).dot(doc_vecs.T)
        highlight_str = sentences[np.argmax(scores)]
        lexical.highlight(highlight_str, takeaway.id)
        highlight = Highlight(takeaway_ptr_id=takeaway.id, quote=highlight_str)

        takeaways_to_create.append(takeaway)
        highlights_to_create.append(highlight)

    # Bulk create takeaways
    Takeaway.objects.bulk_create(takeaways_to_create)

    # Bulk create highlights
    queryset = QuerySet(Highlight)
    queryset._for_write = True
    local_fields = Highlight._meta.local_fields
    with transaction.atomic(using=queryset.db, savepoint=False):
        queryset._batched_insert(highlights_to_create, local_fields, batch_size=None)

    assert note.highlights.count() == len(highlights_to_create)

    note.takeaway_sequence = note_takeaway_sequence
    note.save()
