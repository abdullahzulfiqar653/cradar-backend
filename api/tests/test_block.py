import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.asset import Asset
from api.models.block import Block
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class TestTakeawayRetrieveUpdateDeleteView(APITestCase):
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
        self.project.users.add(self.user)
        self.asset = Asset.objects.create(
            title="asset", project=self.project, created_by=self.user
        )

        self.text_block = Block.objects.create(
            type=Block.Type.TEXT,
            asset=self.asset,
        )
        self.takeaways_block = Block.objects.create(
            type=Block.Type.TAKEAWAYS,
            asset=self.asset,
        )
        self.asset.blocks.add(self.text_block, self.takeaways_block)

        return super().setUp()

    def test_user_retrieve_text_block(self):
        url = f"/api/blocks/{self.text_block.id}/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_block_id = response.json()["id"]
        self.assertEqual(response_block_id, self.text_block.id)

    def test_user_udpate_text_block(self):
        data = {
            "content": {
                "blocks": [
                    {
                        "text": "First line",
                    },
                    {
                        "text": "Second line",
                    },
                ]
            },
        }
        self.client.force_authenticate(self.user)
        url = f"/api/blocks/{self.text_block.id}/"
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.text_block.refresh_from_db()
        self.assertEqual(self.text_block.content, data["content"])

    def test_user_update_block_order(self):
        self.assertEqual(self.text_block.order, 0)
        self.assertEqual(self.takeaways_block.order, 1)
        self.client.force_authenticate(self.user)
        url = f"/api/blocks/{self.takeaways_block.id}/"
        data = {"order": 0}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that text block order is also updated
        self.text_block.refresh_from_db()
        self.takeaways_block.refresh_from_db()
        self.assertEqual(self.takeaways_block.order, 0)
        self.assertEqual(self.text_block.order, 1)
