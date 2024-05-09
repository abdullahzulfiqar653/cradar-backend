import logging
from unittest.mock import patch

import numpy as np
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.asset import Asset
from api.models.block import Block
from api.models.note import Note
from api.models.project import Project
from api.models.takeaway import Takeaway
from api.models.theme import Theme
from api.models.user import User
from api.models.workspace import Workspace


# Create your tests here.
class TestBlockClusterCreateView(APITestCase):
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
        self.theme_block = Block.objects.create(
            type=Block.Type.THEMES,
            asset=self.asset,
        )
        self.asset.blocks.add(self.theme_block)

        # Create themes and add it to the theme_block
        self.theme1 = Theme.objects.create(
            title="theme 1",
            block=self.theme_block,
        )
        self.theme2 = Theme.objects.create(
            title="theme 2",
            block=self.theme_block,
        )

    # We need to patch where it is called, not where it is defined.
    # Ref: https://stackoverflow.com/a/71534298/9577282
    @patch("api.views.block.block_cluster.cluster_block")
    def test_user_call_theme_cluster(self, mocked_cluster_block):
        url = f"/api/blocks/{self.theme_block.id}/cluster/"
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mocked_cluster_block.assert_called_once()
