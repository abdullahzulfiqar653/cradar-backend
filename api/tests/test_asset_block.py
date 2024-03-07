import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.asset import Asset
from api.models.block import Block
from api.models.note import Note
from api.models.project import Project
from api.models.takeaway import Takeaway
from api.models.user import User
from api.models.workspace import Workspace


# Create your tests here.
class TestAssetBlockListCreateView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(username="user", password="password")
        self.outsider = User.objects.create_user(
            username="outsider", password="password"
        )

        workspace = Workspace.objects.create(name="workspace", owned_by=self.user)
        self.project = Project.objects.create(name="project", workspace=workspace)
        self.asset = Asset.objects.create(
            title="asset", project=self.project, created_by=self.user
        )
        self.project.users.add(self.user)
        return super().setUp()

    def test_user_list_asset_block(self):
        note = Note.objects.create(title="note", project=self.project, author=self.user)
        takeaway1 = Takeaway.objects.create(
            title="takeaway 1", note=note, created_by=self.user
        )
        takeaway2 = Takeaway.objects.create(
            title="takeaway 2", note=note, created_by=self.user
        )
        text_block = Block.objects.create(
            asset=self.asset,
            type=Block.Type.TEXT,
            question="question",
            content={"blocks": []},
        )
        takeaways_block = Block.objects.create(
            asset=self.asset,
            type=Block.Type.TAKEAWAYS,
        )
        takeaways_block.takeaways.add(takeaway1, takeaway2)
        url = f"/api/assets/{self.asset.id}/blocks/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_block_ids = [block["id"] for block in response.json()]
        self.assertCountEqual(response_block_ids, [text_block.id, takeaways_block.id])

    def test_user_create_asset_block_without_order(self):
        text_block1 = Block.objects.create(
            asset=self.asset,
            type=Block.Type.TEXT,
            question="question",
            content={"blocks": []},
        )
        text_block2 = Block.objects.create(
            asset=self.asset,
            type=Block.Type.TEXT,
            question="question",
            content={"blocks": []},
        )
        # Block can be created by just specifying the type
        data = dict(type="Text")
        url = f"/api/assets/{self.asset.id}/blocks/"
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data)

        # Check that the block is created at the end if order is not provided
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertCountEqual(
            self.asset.blocks.values("id", "order"),
            [
                {"id": text_block1.id, "order": 0},
                {"id": text_block2.id, "order": 1},
                {"id": response.json()["id"], "order": 2},
            ],
        )

    def test_user_create_asset_block_with_order(self):
        text_block1 = Block.objects.create(
            asset=self.asset,
            type=Block.Type.TEXT,
            question="question",
            content={"blocks": []},
        )
        text_block2 = Block.objects.create(
            asset=self.asset,
            type=Block.Type.TEXT,
            question="question",
            content={"blocks": []},
        )
        data = dict(type="Text", order=1)
        url = f"/api/assets/{self.asset.id}/blocks/"
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data)

        # Check that the block is created at the correct order indicated in the payload
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertCountEqual(
            self.asset.blocks.values("id", "order"),
            [
                {"id": text_block1.id, "order": 0},
                {"id": response.json()["id"], "order": 1},
                {"id": text_block2.id, "order": 2},
            ],
        )

    def test_user_create_asset_block_without_type(self):
        # Block can be created by just specifying the type
        data = dict(type="")
        url = f"/api/assets/{self.asset.id}/blocks/"
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(response.json(), {"type": ['"" is not a valid choice.']})

    def test_user_create_text_asset_block(self):
        # Block can be created by just specifying the type
        data = dict(type="Text")
        url = f"/api/assets/{self.asset.id}/blocks/"
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        block_id = response.json()["id"]
        self.assertTrue(Block.objects.filter(id=block_id).exists())

    def test_user_create_takeaways_asset_block(self):
        data = dict(
            type="Takeaways",
        )
        url = f"/api/assets/{self.asset.id}/blocks/"
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        block_id = response.json()["id"]
        self.assertTrue(Block.objects.filter(id=block_id).exists())

    def test_outsider_list_asset_block(self):
        block1 = Block.objects.create(
            asset=self.asset,
            type=Block.Type.TEXT,
            question="question",
            content={"blocks": []},
        )
        block2 = Block.objects.create(
            asset=self.asset,
            type=Block.Type.TEXT,
            question="question",
            content={"blocks": []},
        )
        url = f"/api/assets/{self.asset.id}/blocks/"
        self.client.force_authenticate(self.outsider)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_create_text_asset_block(self):
        data = dict(
            type="Text",
            question="question",
            content=None,
        )
        url = f"/api/assets/{self.asset.id}/blocks/"
        self.client.force_authenticate(self.outsider)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
