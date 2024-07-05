from django.db.models.query import QuerySet
from langchain.output_parsers.openai_tools import PydanticToolsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic.v1 import BaseModel, Field
from rest_framework import exceptions
from sklearn.cluster import AgglomerativeClustering

from api.ai import config
from api.ai.generators.utils import token_tracker
from api.models.block import Block
from api.models.takeaway import Takeaway
from api.models.user import User


def get_chain():

    class OutputFormatter(BaseModel):
        "Format the output into a JSON object with the given schema"
        title: str = Field(description="Give a title for the takeaway group")

    system_prompt = """
    The following are a group of closely-related takeaways extracted from multiple sources . 
    Generate a title and a description for the takeaway group.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "{text}"),
        ]
    )
    tools = [OutputFormatter]
    llm = ChatOpenAI(model=config.model).bind_tools(
        tools, tool_choice="OutputFormatter"
    )
    parser = PydanticToolsParser(tools=tools)
    chain = prompt | llm | parser
    return chain


def cluster_block(block: Block, takeaways: QuerySet[Takeaway], created_by: User):
    if block.type != Block.Type.THEMES:
        raise exceptions.ValidationError("The block type must be themes.")

    takeaway_count = takeaways.count()
    if takeaway_count < 2:
        raise exceptions.ValidationError("Not enough takeaways to analyze.")
    if takeaway_count > 200:
        raise exceptions.ValidationError("Too many takeaways to analyze.")

    # We only consider takeaways in the same project as block so to not mess up
    takeaways = takeaways.filter(note__project=block.asset.project)

    clustering = AgglomerativeClustering(distance_threshold=1.25, n_clusters=None)
    vectors = [takeaway.vector for takeaway in takeaways]
    labels = clustering.fit_predict(vectors)
    clusters = dict()
    for label, takeaway in zip(labels, takeaways):
        clusters.setdefault(label, []).append(takeaway)

    chain = get_chain()
    block.themes.all().delete()
    for label in range(max(labels)):
        text = "- " + "\n- ".join([takeaway.title for takeaway in clusters[label]])

        with token_tracker(block.asset.project, block, "cluster-block", created_by):
            output = chain.invoke({"text": text})[0]

        theme = block.themes.create(
            title=output.title,
        )
        theme.takeaways.set(clusters[label])
