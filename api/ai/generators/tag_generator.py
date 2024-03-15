import json

from django.db.models.query import QuerySet
from django.utils.translation import gettext
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOpenAI
from pydantic.v1 import BaseModel, Field
from tiktoken import encoding_for_model

from api.ai import config
from api.ai.generators.utils import ParserErrorCallbackHandler, token_tracker
from api.models.note import Note
from api.models.tag import Tag
from api.models.takeaway import Takeaway
from api.models.user import User

__all__ = ["generate_tag"]

encoder = encoding_for_model(config.model)


def generate_tags(note: Note, created_by: User):
    chunked_takeaway_lists = chunk_takeaway_list(note)
    chain = get_chain()

    results = []
    with token_tracker(note.project, note, "generate-tags", created_by):
        for takeaway_list in chunked_takeaway_lists:
            data = {"takeaways": takeaway_list}
            takeaways = json.dumps(data)
            result = chain.invoke(
                {"takeaways": takeaways},
                config={"callbacks": [ParserErrorCallbackHandler()]},
            )
            results.extend(result.dict()["takeaways"])
    tags = save_tags(note, results)
    save_takeaway_tags(note, tags, results)


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
                    "Assign a list of tags for each string in the provided list. "
                    "Tags should succinctly describe "
                    "the content or topic of each string. "
                    "Ensure that the tags are relevant and descriptive. "
                    "Output the response in JSON format such as the following example. "
                    f"Example: {example}"
                ),
            ),
            ("human", "{takeaways}"),
        ],
    )
    parser = PydanticOutputParser(pydantic_object=TakeawayListSchema)
    chain = prompt | llm.bind(response_format={"type": "json_object"}) | parser
    return chain


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


def save_takeaway_tags(note: Takeaway, tags: QuerySet[Tag], results):
    get_tag = {tag.name.lower(): tag for tag in tags}
    get_takeaway = {takeaway.id: takeaway for takeaway in note.takeaways.all()}
    TakeawayTag = Takeaway.tags.through
    takeaway_tags = []
    for takeaway_data in results:
        takeaway: Takeaway = get_takeaway[takeaway_data["id"]]
        for tag_name in takeaway_data["tags"]:
            tag = get_tag[tag_name.lower()]
            takeaway_tags.append(TakeawayTag(takeaway=takeaway, tag=tag))
    TakeawayTag.objects.bulk_create(takeaway_tags, ignore_conflicts=True)
