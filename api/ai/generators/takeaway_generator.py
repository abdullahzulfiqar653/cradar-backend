from textwrap import dedent

from django.db.models import QuerySet
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.schema.document import Document
from langchain.text_splitter import TokenTextSplitter
from langchain_openai.chat_models import ChatOpenAI
from nltk.tokenize import sent_tokenize
from pydantic.v1 import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer

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


def get_chain(takeaway_type: TakeawayType):
    system_prompt = dedent(
        """
            You are tasked with extracting specific information from a given transcript. Here are the details:

            Extraction Name:
            <extraction_name>
            {{EXTRACTION_NAME}}
            </extraction_name>

            Extraction Definition:
            <extraction_definition>
            {{EXTRACTION_DEFINITION}}
            </extraction_definition>

            Now, carefully read and analyze the following transcript:

            <transcript>
            {{TRANSCRIPT}}
            </transcript>

            Your task is to extract key takeaways from the transcript based on the extraction name and definition provided. Follow these steps:

            1. Identify the main topics discussed in the transcript that relate to the extraction name and definition.

            2. For each relevant topic, determine:
                a) The key insight or information presented
                b) The significance or importance of this insight
                c) A verbatim quote from the transcript that best supports this takeaway

            3. Format your findings into a JSON structure with the following format:
                {
                    "takeaways": [
                        {
                            "topic": "<topic of the takeaway>",
                            "insight": "<the insight of the takeaway>",
                            "significance": "<the significance of the takeaway>",
                            "quote": "<the verbatim quote from the transcript that supports the takeaway>"
                        }
                    ]
                }

            4. Ensure that each takeaway is directly related to the extraction name and definition.

            5. Limit your response to the most important and relevant takeaways. Typically, this should be between 3-5 takeaways, but use your judgment based on the transcript's content and the specificity of the extraction requirements.

            6. Double-check that all quotes are exact matches from the transcript.

            7. Make sure the JSON is properly formatted and valid.

            <example_output>
            {
                "takeaways": [
                    {
                        "topic": "Poor Onboarding Experience",
                        "insight": "This user complains that the onboarding and setup experience is terrible and does not know how to get to the core value of the software",
                        "significance": "[The significance of the takeaway]",
                        "quote": "[the verbatim quote from the transcript that supports the takeaway]"
                    },
                    {
                        "topic": "Automated User Research and Automated Tagging",
                        "insight": "This user was delighted that the software automated away all of their manual tasks for user research when it automatically tagged all the notes that the user created",
                        "significance": "[The significance of the takeaway]",
                        "quote": "[the verbatim quote from the transcript that supports the takeaway]"
                    },
                    {
                        "topic": "Not doing enough user interviews",
                        "insight": "[User's name] mentioned that they would like to be able to do more interviews on their customer brands and investigate what are their problems. This would then allow them to identify problem statements that they can solve for their customer brands",
                        "significance": "[The significance of the takeaway]",
                        "quote": "[the verbatim quote from the transcript that supports the takeaway]"
                    },
                ]
            }
            </example_output>

            Output only the JSON structure with your findings, without any additional text or explanation.
        """
    )

    class TakeawaySchema(BaseModel):
        topic: str
        insight: str
        significance: str
        quote: str

    class TakeawaysSchema(BaseModel):
        takeaways: list[TakeawaySchema]

    llm = ChatOpenAI(model=config.model)
    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt)],
        template_format="jinja2",
    )
    parser = PydanticOutputParser(pydantic_object=TakeawaysSchema)
    chain = prompt | llm.bind(response_format={"type": "json_object"}) | parser
    return chain


def generate_takeaways(
    note: Note, takeaway_types: QuerySet[TakeawayType], created_by: User
):
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
            {
                "takeaway_type": takeaway_type,
                "output": get_chain(takeaway_type).invoke(
                    {
                        "TRANSCRIPT": doc.page_content,
                        "EXTRACTION_NAME": takeaway_type.name,
                        "EXTRACTION_DEFINITION": takeaway_type.definition,
                    },
                    config={"callbacks": [ParserErrorCallbackHandler()]},
                ),
            }
            for takeaway_type in takeaway_types
            for doc in docs
        ]

    if not outputs:
        return

    generated_takeaways = [
        {
            "title": google_translator.translate(
                f'Topic: {takeaway["topic"]} - {takeaway["insight"].rstrip(".")}: {takeaway["significance"]}',
                note.project.language,
            ),
            "quote": takeaway["quote"],
            "takeaway_type": output["takeaway_type"],
        }
        for output in outputs
        for takeaway in output["output"].dict()["takeaways"]
    ]

    # Embed note content
    lexical = LexicalProcessor(note.content["root"])
    sentences = [
        sentence.strip()
        for paragraph in lexical.to_text().split("\n")
        for sentence in sent_tokenize(paragraph)
        if sentence.strip()  # Check if there is some text after stripping
    ]
    bi_sentences = [
        f"{sentence1} {sentence2}"
        for sentence1, sentence2 in zip(sentences[:-1], sentences[1:])
    ]
    tri_sentences = [
        f"{sentence1} {sentence2} {sentence3}"
        for sentence1, sentence2, sentence3 in zip(
            sentences[:-2], sentences[1:-1], sentences[2:]
        )
    ]
    sentences.extend(bi_sentences)
    sentences.extend(tri_sentences)
    vectorizer = TfidfVectorizer()
    doc_vecs = vectorizer.fit_transform(sentences)

    # Find best matches
    generated_takeaway_quotes = [takeaway["quote"] for takeaway in generated_takeaways]
    quote_vectors = vectorizer.transform(generated_takeaway_quotes)
    cosine_similarities = quote_vectors.dot(doc_vecs.T)
    best_matches = cosine_similarities.argmax(axis=1).A1

    # Embed generated takeaways
    generated_takeaway_titles = [takeaway["title"] for takeaway in generated_takeaways]
    generated_takeaway_vectors = embedder.embed_documents(generated_takeaway_titles)

    # Create takeaways
    takeaways_to_create = []
    highlights_to_create = []
    for generated_takeaway, vector, index in zip(
        generated_takeaways, generated_takeaway_vectors, best_matches
    ):

        takeaway = Takeaway(
            title=generated_takeaway["title"],
            vector=vector,
            note=note,
            created_by=bot,
            type=generated_takeaway["takeaway_type"],
        )

        highlight_str = sentences[index]
        lexical.highlight(highlight_str, takeaway.id)
        highlight = Highlight(takeaway_ptr_id=takeaway.id, quote=highlight_str)

        takeaways_to_create.append(takeaway)
        highlights_to_create.append(highlight)

    Takeaway.objects.bulk_create(takeaways_to_create)
    Highlight.bulk_create(highlights_to_create)

    # Update note.content
    note.save()
