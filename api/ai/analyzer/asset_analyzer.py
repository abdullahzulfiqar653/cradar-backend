from django.db.models import QuerySet

from api.ai.generators.asset_generator import generate_content
from api.ai.generators.block_clusterer import cluster_block
from api.models.asset import Asset
from api.models.block import Block
from api.models.takeaway import Takeaway
from api.models.takeaway_type import TakeawayType
from api.models.user import User
from api.utils.lexical import LexicalProcessor
from api.utils.markdown import MarkdownProcessor


def create_lexical_from_markdown(markdown: str):
    lexical_json = MarkdownProcessor(markdown).to_lexical()
    return LexicalProcessor(lexical_json["root"])


class AssetAnalyzer:
    def analyze(
        self,
        asset: Asset,
        takeaway_types: QuerySet[TakeawayType],
        created_by: User,
    ):
        # Cluster for each takeaway type
        print("========> Clustering takeaways")
        lexical = LexicalProcessor(asset.content["root"])
        takeaways = Takeaway.objects.filter(note__assets=asset)
        for takeaway_type in takeaway_types:
            print("  ========> Clustering takeaway type:", takeaway_type.name)
            filtered_takeaways = takeaways.filter(type=takeaway_type)
            if filtered_takeaways.count() > 200:
                raise ValueError(
                    f"Too many takeaways to analyze for takeaway type '{takeaway_type.name}'. "
                    "Please reduce to 200 takeaways and try again."
                )
            block_title = create_lexical_from_markdown(f"**{takeaway_type}:**")
            lexical.append(block_title)
            block = asset.blocks.create(type=Block.Type.THEMES)
            print("  ========> Block created.")
            cluster_block(block, filtered_takeaways, created_by)
            lexical.add_block(block)

        print("========> Generating recommendations")
        question = "Based on the themes, please recommends the next steps."
        markdown = generate_content(asset, question, [], created_by)
        output = create_lexical_from_markdown(markdown)
        lexical.append(output)

        print("========> Generating summary")
        question = "Write a single paragraph executive summary for this report."
        markdown = generate_content(asset, question, [], created_by)
        output = create_lexical_from_markdown(markdown)
        output.append(lexical)

        print("========> Generating title")
        question = "Give a short and concise title for this report. Do not repeat the content. Do not format."
        title = generate_content(asset, question, [], created_by)
        asset.title = title.replace("<cursor/>", "")

        asset.content["root"] = output.dict
        asset.save()
        print("========> End analyzing")
