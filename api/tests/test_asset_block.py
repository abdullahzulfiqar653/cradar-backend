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
class TestAssetBlockListView(APITestCase):
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

    def test_user_list_asset_block(self):
        url = f"/api/assets/{self.asset.id}/blocks/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_block_ids = [block["id"] for block in response.json()]
        self.assertCountEqual(
            response_block_ids, [self.takeaways_block.id, self.themes_block.id]
        )

    def test_outsider_list_asset_block(self):
        url = f"/api/assets/{self.asset.id}/blocks/"
        self.client.force_authenticate(self.outsider)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
