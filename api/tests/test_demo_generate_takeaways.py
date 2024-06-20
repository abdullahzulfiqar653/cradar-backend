import logging
from unittest.mock import MagicMock, patch

import numpy as np
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.project import Project
from api.models.takeaway_type import TakeawayType
from api.models.user import User
from api.models.workspace import Workspace


class TestDemoGenerateTakeawaysCreateView(APITestCase):
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
        return super().setUp()

    @patch("api.ai.analyzer.note_analyzer.NewNoteAnalyzer.analyze")
    def test_demo_generate_takeaways(self, mocked_invoke: MagicMock):
        def side_effect(note, user):
            takeaway_type = TakeawayType.objects.create(
                name="takeaway type 1",
                project=self.project,
                vector=np.random.rand(1536),
            )
            note.takeaways.create(
                title="Takeaway 1 title",
                type=takeaway_type,
                created_by=self.user,
                vector=np.random.rand(1536),
            )
            note.takeaways.create(
                title="Takeaway 2 title",
                type=takeaway_type,
                created_by=self.user,
                vector=np.random.rand(1536),
            )

        mocked_invoke.side_effect = side_effect

        with self.settings(DEMO_PROJECT_ID=self.project.id, DEMO_USER_ID=self.user.id):
            url = "/api/demo/takeaways/"
            data = {
                "is_published": False,
                "keywords": [],
                "url": "www.example.com",
            }
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            expected_takeaway_titles = ["Takeaway 1 title", "Takeaway 2 title"]
            response_takeaway_titles = [
                takeaway["title"] for takeaway in response.json()
            ]
            self.assertCountEqual(expected_takeaway_titles, response_takeaway_titles)
