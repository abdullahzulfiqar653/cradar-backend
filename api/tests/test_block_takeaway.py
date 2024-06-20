import logging

import numpy as np
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
class TestBlockTakeawayListCreateView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(username="user", password="password")
        self.outsider = User.objects.create_user(
            username="outsider", password="password"
        )

        self.workspace = Workspace.objects.create(name="workspace", owned_by=self.user)
        self.workspace.members.add(self.user, through_defaults={"role": "Editor"})
        self.project = Project.objects.create(name="project", workspace=self.workspace)
        self.project.users.add(self.user)

        self.note = Note.objects.create(
            title="note", project=self.project, author=self.user
        )
        self.takeaway1 = Takeaway.objects.create(
            title="takeaway 1",
            note=self.note,
            created_by=self.user,
            vector=np.random.rand(1536),
        )
        self.takeaway2 = Takeaway.objects.create(
            title="takeaway 2",
            note=self.note,
            created_by=self.user,
            vector=np.random.rand(1536),
        )

        self.asset = Asset.objects.create(
            title="asset", project=self.project, created_by=self.user
        )
        self.takeaway_block = Block.objects.create(
            type=Block.Type.TAKEAWAYS,
            asset=self.asset,
        )
        self.theme_block = Block.objects.create(
            type=Block.Type.THEMES,
            asset=self.asset,
        )
        self.asset.blocks.add(self.takeaway_block, self.theme_block)
        self.takeaway_block.takeaways.add(self.takeaway1)

    def test_user_list_block_takeaways(self):
        url = f"/api/blocks/{self.takeaway_block.id}/takeaways/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_takeaway_ids = [takeaway["id"] for takeaway in response.json()]
        self.assertCountEqual(response_takeaway_ids, [self.takeaway1.id])

    def test_user_add_takeaways_to_theme_block(self):
        "We do not allow adding takeaways to theme block."
        data = {"takeaways": [{"id": self.takeaway2.id}]}
        url = f"/api/blocks/{self.theme_block.id}/takeaways/"
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_add_takeaways_to_takeaway_block(self):
        data = {"takeaways": [{"id": self.takeaway2.id}]}
        url = f"/api/blocks/{self.takeaway_block.id}/takeaways/"
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertCountEqual(
            self.takeaway_block.takeaways.all(), [self.takeaway1, self.takeaway2]
        )

    def test_user_delete_takeaways_from_takeaway_block(self):
        data = {"takeaways": [{"id": self.takeaway1.id}]}
        url = f"/api/blocks/{self.takeaway_block.id}/takeaways/delete/"
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(self.takeaway_block.takeaways.all(), [])

    def test_outsider_list_block_takeaways(self):
        url = f"/api/blocks/{self.takeaway_block.id}/takeaways/"
        self.client.force_authenticate(self.outsider)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_add_takeaways_to_takeaway_block(self):
        data = {"takeaways": [{"id": self.takeaway2.id}]}
        url = f"/api/blocks/{self.takeaway_block.id}/takeaways/"
        self.client.force_authenticate(self.outsider)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
