import json

from django.db.models.query import QuerySet
from django.utils.translation import gettext
from langchain.callbacks.base import BaseCallbackHandler
from langchain.output_parsers.openai_functions import PydanticOutputFunctionsParser
from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain_community.utils.openai_functions import (
    convert_pydantic_to_openai_function,
)
from pydantic.v1 import BaseModel, Field
from tiktoken import encoding_for_model

from api.ai import config
from api.ai.generators.utils import token_tracker
from api.models.note import Note
from api.models.tag import Tag
from api.models.takeaway import Takeaway
from api.models.user import User

__all__ = ["generate_tag"]

encoder = encoding_for_model(config.model)


class ParserErrorCallbackHandler(BaseCallbackHandler):
    def on_chain_start(self, *args, **kwargs):
        if kwargs.get("run_type") == "parser":
            self.ai_message = args[1]

    def on_chain_error(self, *args, **kwargs):
        if hasattr(self, "ai_message"):
            print(self.ai_message)


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
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                gettext(
                    "Give each of the takeaways a list of tags. "
                    "Do not include the messages."
                ),
            ),
            ("human", "{takeaways}"),
        ],
    )
    function = convert_pydantic_to_openai_function(TakeawayListSchema)
    function_call = {"name": function["name"]}
    parser = PydanticOutputFunctionsParser(pydantic_schema=TakeawayListSchema)
    chain = (
        prompt
        | llm.bind(
            functions=[function],
            function_call=function_call,
        )
        | parser
    )
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
