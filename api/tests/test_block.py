import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.asset import Asset
from api.models.block import Block
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class TestBlockRetrieveView(APITestCase):
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
        workspace.members.add(self.user, through_defaults={"role": "Editor"})
        self.project = Project.objects.create(name="project", workspace=workspace)
        self.project.users.add(self.user)
        self.asset = Asset.objects.create(
            title="asset", project=self.project, created_by=self.user
        )

        self.takeaways_block = Block.objects.create(
            type=Block.Type.TAKEAWAYS,
            asset=self.asset,
        )
        self.asset.blocks.add(self.takeaways_block)

        return super().setUp()

    def test_user_retrieve_takeaways_block(self):
        url = f"/api/blocks/{self.takeaways_block.id}/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_block_id = response.json()["id"]
        self.assertEqual(response_block_id, self.takeaways_block.id)

    def test_outsider_retrieve_takeaways_block(self):
        url = f"/api/blocks/{self.takeaways_block.id}/"
        self.client.force_authenticate(self.outsider)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
