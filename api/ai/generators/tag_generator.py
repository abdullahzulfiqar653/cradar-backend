import json
import numpy as np
from tiktoken import encoding_for_model
from pydantic.v1 import BaseModel, Field
from pgvector.django import MaxInnerProduct
from django.db.models.query import QuerySet
from django.utils.translation import gettext
from langchain.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser

from api.models.tag import Tag
from api.models.note import Note
from api.models.user import User
from api.models.takeaway import Takeaway
from api.ai import config
from api.ai.embedder import embedder
from api.ai.generators.utils import ParserErrorCallbackHandler, token_tracker

__all__ = ["generate_tag"]

encoder = encoding_for_model(config.model)


def get_chain():
    class TakeawaySchema(BaseModel):
        __doc__ = gettext("The id and the corresponding tags.")

        id: str = Field(
            description=gettext("ID of the takeaway. For example: '322xBv9XpAbD'")
        )
        tags: list[str] = Field(
            description=gettext("What is the list of tags for this takeaway?")
        )

    class TakeawayListSchema(BaseModel):
        __doc__ = gettext("""A list of takeaways with their relevant tags.""")

        takeaways: list[TakeawaySchema]

    llm = ChatOpenAI(model=config.model)
    example = (
        json.dumps(
            {
                "takeaways": [
                    {
                        "id": "322xBv9XpAbD",
                        "tags": ["tag 1", "tag 2"],
                    },
                    {
                        "id": "m84P4opD89At",
                        "tags": ["tag 1", "tag 3"],
                    },
                ]
            },
        )
        .replace("{", "{{")
        .replace("}", "}}")
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                gettext(
                    "Assign the provided list of tags to each string in the provided list of takeaways. "
                    "Ensure that the tags are relevant. "
                    "Use only the tags provided and do not generate new tags. "
                    "Output the response in JSON format such as the following example. "
                    f"Example: {example}"
                ),
            ),
            ("human", "{takeaways_and_tags}"),
        ],
    )
    parser = PydanticOutputParser(pydantic_object=TakeawayListSchema)
    chain = prompt | llm.bind(response_format={"type": "json_object"}) | parser
    return chain


def generate_tags(note: Note, created_by: User):
    chain = get_chain()
    chunked_takeaway_lists = chunk_takeaway_list(note)
    tags = list(note.project.tags.all().values_list('name', flat=True))

    results = []
    with token_tracker(note.project, note, "generate-tags", created_by):
        for takeaway_list in chunked_takeaway_lists:
            data = {
                "takeaways_and_tags": {
                    "takeaways": takeaway_list,
                    "tags": tags,
                }
            }
            takeaways_and_tags = json.dumps(data)
            result = chain.invoke(
                {"takeaways_and_tags": takeaways_and_tags},
                config={"callbacks": [ParserErrorCallbackHandler()]},
            )
            results.extend(result.dict()["takeaways"])
    save_takeaway_tags(note, results)


def chunk_takeaway_list(note: Note):
    token_count = 0
    chunked_takeaway_lists = [[]]
    for takeaway in note.takeaways.all():
        token_count += len(encoder.encode(takeaway.title))
        if token_count < config.chunk_size:
            chunked_takeaway_lists[-1].append(
                {"id": takeaway.id, "message": takeaway.title}
            )
        else:  # token_count >= config.chunk_size
            chunked_takeaway_lists.append(
                [{"id": takeaway.id, "message": takeaway.title}]
            )
            token_count = 0
    return chunked_takeaway_lists


def save_tags(note: Note, results) -> QuerySet[Tag]:
    tags_to_add = [
        Tag(name=tag_name, project=note.project)
        for takeaway in results
        for tag_name in takeaway["tags"]
    ]
    Tag.objects.bulk_create(tags_to_add, ignore_conflicts=True)
    tag_names = [tag.name for tag in tags_to_add]
    tags = Tag.objects.filter(name__in=tag_names, project=note.project)
    return tags


def save_takeaway_tags(note: Takeaway, results):
    get_takeaway = {takeaway.id: takeaway for takeaway in note.takeaways.all()}
    for takeaway_data in results:
        takeaway: Takeaway = get_takeaway[takeaway_data["id"]]
        for tag_name in takeaway_data["tags"]:
            query_vector = embedder.embed_query(tag_name)
            blank_vector = embedder.embed_documents([""])[0]
            threshold = np.array(query_vector).dot(np.array(blank_vector))
            matched_tag = (
                Tag.objects.filter(project=note.project)
                .annotate(score=-MaxInnerProduct("vector", query_vector))
                .filter(score__gt=threshold)
                .first()
            )
            if matched_tag:
                takeaway.tags.add(matched_tag)
