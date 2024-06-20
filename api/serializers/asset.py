from rest_framework import serializers

from api.models.asset import Asset
from api.models.block import Block
from api.serializers.user import UserSerializer
from api.utils.lexical import LexicalProcessor


class AssetSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Asset
        fields = [
            "id",
            "title",
            "description",
            "filter",
            "content",
            "created_at",
            "updated_at",
            "created_by",
        ]
        extra_kwargs = {"filter": {"default": ""}}

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["project"] = request.project
        validated_data["created_by"] = request.user
        return super().create(validated_data)

    def update(self, asset: Asset, validated_data):
        if "content" in validated_data:
            self.update_content_blocks(asset, validated_data)
        return super().update(asset, validated_data)

    def update_content_blocks(self, asset: Asset, validated_data):
        lexical = LexicalProcessor(validated_data["content"]["root"])
        nodes = list(lexical.find_all("Takeaways"))
        nodes.extend(list(lexical.find_all("Themes")))

        # Delete blocks
        block_ids = {node.dict["block_id"] for node in nodes if node.dict["block_id"]}
        asset.blocks.exclude(id__in=block_ids).delete()

        # Drop nodes that do not belong to the asset
        faulty_block_ids = set(
            Block.objects.filter(id__in=block_ids)
            .exclude(asset=asset)
            .values_list("id", flat=True)
        )
        for node in nodes:
            if node.dict["block_id"] in faulty_block_ids:
                node.parent.dict["children"].remove(node.dict)

        # Create blocks
        blocks_to_create = []
        for node in nodes:
            if node.dict["block_id"]:
                continue

            block = Block(
                asset=asset,
                type=node.dict["type"],
            )
            node.dict["block_id"] = block.id
            blocks_to_create.append(block)

        Block.objects.bulk_create(blocks_to_create)


class AssetGenerateSerializer(serializers.Serializer):
    filter = serializers.CharField(
        write_only=True,
        help_text="The url query string to filter takeaways.",
        default=None,
    )
    question = serializers.CharField(write_only=True)
    markdown = serializers.CharField(read_only=True)

    class Meta:
        fields = ["filter", "markdown", "question"]

    def create(self, validated_data):
        return super().create(validated_data)
