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
from api.models.user import User
from api.models.workspace import Workspace


# Create your tests here.
class TestAssetGenerateCreateView(APITestCase):
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

    def test_user_generate_block_with_blank_question(self):
        "Cannot generate text block without question or with blank question"
        url = f"/api/assets/{self.asset.id}/generate/"
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(url, data={"question": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("langchain_core.runnables.base.RunnableSequence.invoke")
    def test_user_generate_block(self, mocked_invoke):
        class Output:
            content = "Generated results."

        mocked_invoke.return_value = Output()

        url = f"/api/assets/{self.asset.id}/generate/"
        self.client.force_authenticate(self.user)
        response = self.client.post(
            url,
            data={
                "filter": "priority=High",
                "instruction": "What is this?",
            },
        )

        mocked_invoke.assert_called_once()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Backend only returns the markdown, frontend will be responsible for updating the content
        self.assertEqual(response.json()["markdown"], "Generated results.")
