from unittest.mock import patch

from rest_framework.test import APITestCase

from api.models.message import Message
from api.models.note import Note
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class TestNoteMessageListCreateView(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="user", password="password")
        self.outsider = User.objects.create_user(
            username="outsider", password="password"
        )

        workspace = Workspace.objects.create(name="workspace", owned_by=self.user)
        workspace.members.add(self.user, through_defaults={"role": "Editor"})
        self.project = Project.objects.create(name="project", workspace=workspace)
        self.project.users.add(self.user)

        self.note = Note.objects.create(
            title="note",
            project=self.project,
            author=self.user,
        )
        self.note.content = {
            "root": {
                "children": [
                    {
                        "children": [
                            {
                                "text": "Sample paragraph 1.",
                                "type": "text",
                            },
                        ],
                        "type": "paragraph",
                    },
                    {
                        "children": [
                            {
                                "text": "Sample paragraph 2.",
                                "type": "text",
                            },
                        ],
                        "type": "paragraph",
                    },
                ],
                "type": "root",
            }
        }
        self.note.save()

        bot = User.objects.get(email="bot@raijin.ai")
        self.message1 = self.note.messages.create(
            user=self.user,
            text="Message 1",
            note=self.note,
            role=Message.Role.HUMAN,
        )
        self.message2 = self.note.messages.create(
            user=bot,
            text="AI response",
            note=self.note,
            role=Message.Role.HUMAN,
        )
        return super().setUp()

    def test_user_list_messages(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/reports/{self.note.id}/messages/")
        self.assertEqual(response.status_code, 200)
        expected_data = [
            {
                "id": self.message1.id,
                "text": "Message 1",
                "role": "human",
                "order": 0,
                "user": {
                    "email": self.user.email,
                    "first_name": self.user.first_name,
                    "last_name": self.user.last_name,
                },
                "created_at": self.message1.created_at.strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
                "updated_at": self.message1.updated_at.strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
            },
            {
                "id": self.message2.id,
                "text": "AI response",
                "role": "human",
                "order": 1,
                "user": {
                    "email": "bot@raijin.ai",
                    "first_name": "Created by AI",
                    "last_name": "",
                },
                "created_at": self.message2.created_at.strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
                "updated_at": self.message2.updated_at.strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
            },
        ]
        self.assertCountEqual(response.json(), expected_data)

    @patch("langchain_core.runnables.base.RunnableSequence.invoke")
    def test_user_create_message(self, mocked_invoke):
        class MockedOutput:
            def __init__(self, content):
                self.content = content

        self.client.force_authenticate(user=self.user)
        mocked_invoke.return_value = MockedOutput("Generated AI response")
        response = self.client.post(
            f"/api/reports/{self.note.id}/messages/",
            {
                "text": "User message",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["text"], "Generated AI response")
        self.assertEqual(response.json()["role"], Message.Role.AI)
        self.assertEqual(response.json()["text"], "Generated AI response")
        self.assertEqual(self.note.messages.count(), 4)
