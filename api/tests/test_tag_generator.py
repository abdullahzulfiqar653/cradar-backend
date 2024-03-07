import logging
from unittest.mock import MagicMock, patch

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.note import Note
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class TestNoteTagGenerateView(APITestCase):
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

        self.note = Note.objects.create(
            title="Sample report",
            project=self.project,
            author=self.user,
            type="Report-type-1",
        )
        self.takeaway1 = self.note.takeaways.create(
            title="takeaway 1", created_by=self.user
        )
        self.takeaway2 = self.note.takeaways.create(
            title="takeaway 1", created_by=self.user
        )
        return super().setUp()

    @patch("langchain_core.runnables.base.RunnableSequence.invoke")
    def test_generate_tag(self, mocked_invoke: MagicMock):
        class MockedTakeawayListSchema:
            def dict():
                return {
                    "takeaways": [
                        {
                            "id": self.takeaway1.id,
                            "tags": [
                                "takeaway1 - tag1",
                                "takeaway1 - tag2",
                            ],
                        },
                        {
                            "id": self.takeaway2.id,
                            "tags": [
                                "takeaway2 - tag1",
                                "takeaway2 - tag2",
                            ],
                        },
                    ],
                }

        mocked_invoke.return_value = MockedTakeawayListSchema

        self.client.force_authenticate(self.user)
        url = f"/api/reports/{self.note.id}/tags/generate/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mocked_invoke.assert_called_once()

        self.takeaway1.refresh_from_db()
        self.assertCountEqual(
            self.takeaway1.tags.values_list("name", flat=True),
            ["takeaway1 - tag1", "takeaway1 - tag2"],
        )
        self.assertCountEqual(
            self.takeaway2.tags.values_list("name", flat=True),
            ["takeaway2 - tag1", "takeaway2 - tag2"],
        )
