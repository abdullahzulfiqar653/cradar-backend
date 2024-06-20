import datetime
import logging
from copy import deepcopy

import numpy as np
from dateutil import parser
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
class TestAssetRetrieveUpdateDeleteView(APITestCase):
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
        self.takeaways_block = Block.objects.create(
            asset=self.asset,
            type=Block.Type.TAKEAWAYS,
        )
        self.themes_block = Block.objects.create(
            asset=self.asset,
            type=Block.Type.THEMES,
        )
        self.asset.content = {
            "root": {
                "type": "Root",
                "children": [
                    {
                        "type": "paragraph",
                        "format": "",
                        "indent": 0,
                        "version": 1,
                        "children": [
                            {
                                "mode": "normal",
                                "text": "This is some text",
                                "type": "text",
                                "style": "",
                                "detail": 0,
                                "format": 0,
                                "version": 1,
                            }
                        ],
                        "direction": "ltr",
                    },
                    {
                        "type": "Takeaways",
                        "block_id": self.takeaways_block.id,
                        "version": 1,
                    },
                    {
                        "type": "Themes",
                        "block_id": self.themes_block.id,
                        "version": 1,
                    },
                ],
            }
        }
        self.takeaways_block.takeaways.add(self.takeaway1, self.takeaway2)
        return super().setUp()

    def test_user_retrieve_asset_details(self):
        self.client.force_authenticate(self.user)
        url = f"/api/assets/{self.asset.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["title"], "asset")

    def test_user_cannot_update_asset_created_at(self):
        self.client.force_authenticate(self.user)
        url = f"/api/assets/{self.asset.id}/"
        now_utc = datetime.datetime.now().astimezone(datetime.timezone.utc)
        data = {"created_at": now_utc}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_created_at = parser.parse(response.json()["created_at"]).astimezone(
            datetime.timezone.utc
        )
        self.assertEqual(response_created_at, self.asset.created_at)

    def test_user_add_asset_block(self):
        self.client.force_authenticate(self.user)
        url = f"/api/assets/{self.asset.id}/"
        content = deepcopy(self.asset.content)
        content["root"]["children"].append(
            {
                "type": "Themes",
                "block_id": None,
                "version": 1,
            }
        )
        response = self.client.patch(url, {"content": content})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.asset.blocks.count(), 3)

    def test_user_add_multiple_same_asset_block(self):
        self.client.force_authenticate(self.user)
        url = f"/api/assets/{self.asset.id}/"
        content = deepcopy(self.asset.content)
        content["root"]["children"].append(
            {
                "type": "Themes",
                "block_id": self.themes_block.id,
                "version": 1,
            }
        )
        response = self.client.patch(url, {"content": content})
        # There shouldn't be any issue with multiple blocks pointing to the same id
        # Frontend will just render the same block multiple times
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.asset.blocks.count(), 2)

    def test_user_remove_asset_block(self):
        self.client.force_authenticate(self.user)
        url = f"/api/assets/{self.asset.id}/"
        content = deepcopy(self.asset.content)
        assert content["root"]["children"][-1]["type"] == "Themes"
        content["root"]["children"].pop()
        response = self.client.patch(url, {"content": content})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.asset.blocks.count(), 1)

    def test_user_delete_asset(self):
        self.client.force_authenticate(self.user)
        url = f"/api/assets/{self.asset.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_retrieve_asset_details(self):
        self.client.force_authenticate(self.outsider)
        url = f"/api/assets/{self.asset.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_delete_insight(self):
        self.client.force_authenticate(self.outsider)
        url = f"/api/assets/{self.asset.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
