import datetime

import numpy as np
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings.openai import OpenAIEmbeddings
from langchain_community.utils.openai_functions import (
    convert_pydantic_to_openai_function,
)
from pydantic import BaseModel, Field
from sklearn.cluster import HDBSCAN

from api.ai import config
from api.ai.generators.utils import token_tracker
from api.models.project import Project
from api.models.takeaway import Takeaway
from api.models.user import User


def get_chain():
    class Cluster(BaseModel):
        "A cluster."
        cluster: str = Field('The given cluster name. For example, "Cluster 0".')
        topic: str = Field("The topic to be assigned for the cluster.")

    class Clusters(BaseModel):
        "A collection of cluster."
        clusters: list[Cluster]

    llm = ChatOpenAI(model=config.model)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Assign a topic for each of the given clusters."),
            ("human", "{clusters}"),
        ]
    )
    openai_functions = [convert_pydantic_to_openai_function(Clusters)]
    parser = JsonOutputFunctionsParser()
    chain = prompt | llm.bind(functions=openai_functions) | parser
    return chain


def cluster_project(project: Project, created_by: User):
    current_time = datetime.datetime.now().astimezone(datetime.timezone.utc)
    cutoff = current_time - datetime.timedelta(weeks=1)
    embedder = OpenAIEmbeddings()
    takeaways = Takeaway.objects.filter(note__project=project).filter(
        created_at__gt=cutoff
    )
    takeaway_titles = takeaways.values_list("title", flat=True)

    if len(takeaway_titles) < 5:
        return

    takeaway_vectors = np.array(embedder.embed_documents(takeaway_titles))
    clustering = HDBSCAN(min_cluster_size=3)
    clustering.fit(takeaway_vectors)

    if max(clustering.labels_) <= 0:
        return

    clusters = dict()
    for cluster_id in range(max(clustering.labels_)):
        clusters[f"Cluster {cluster_id}"] = [
            takeaway_titles[int(i)]
            for i in np.argwhere(clustering.labels_ == cluster_id).flatten()
        ]

    text = "\n\n".join(
        [
            f"{key}:\n" + "  * " + "\n  * ".join(cluster)
            for key, cluster in clusters.items()
        ]
    )

    chain = get_chain()
    with token_tracker(project, project, "cluster-takeaways", created_by):
        output = chain.invoke({"clusters": text})
    key_themes = [
        {
            "title": cluster_topic["topic"],
            "takeaways": clusters[cluster_topic["cluster"]],
        }
        for cluster_topic in output["clusters"]
    ]
    project.key_themes = key_themes
    project.save()
