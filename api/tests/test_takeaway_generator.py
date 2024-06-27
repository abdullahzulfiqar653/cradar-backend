import logging
from unittest.mock import MagicMock, patch

import numpy as np
from rest_framework.test import APITestCase

from api.ai.generators.takeaway_generator import generate_takeaways
from api.models.note import Note
from api.models.note_type import NoteType
from api.models.project import Project
from api.models.takeaway_type import TakeawayType
from api.models.user import User
from api.models.workspace import Workspace


class TestTakeawayGenerator(APITestCase):
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

        self.note_type1 = NoteType.objects.create(
            name="Report-type-1", project=self.project, vector=np.random.rand(1536)
        )
        self.note_type2 = NoteType.objects.create(
            name="Report-type-2", project=self.project, vector=np.random.rand(1536)
        )

        self.note = Note.objects.create(
            title="Sample report",
            project=self.project,
            author=self.user,
            type=self.note_type1,
            content={
                "root": {
                    "children": [
                        {
                            "children": [
                                {
                                    "text": "This is a sample text only.",
                                    "type": "text",
                                }
                            ],
                            "type": "paragraph",
                        },
                        {
                            "children": [
                                {
                                    "text": "This is a sample text in the second block.",
                                    "type": "text",
                                }
                            ],
                            "type": "paragraph",
                        },
                    ],
                    "type": "root",
                }
            },
        )
        self.takeaway_type1 = TakeawayType.objects.create(
            name="Takeaway-type-1", project=self.project
        )
        self.takeaway_type2 = TakeawayType.objects.create(
            name="Takeaway-type-2", project=self.project
        )
        return super().setUp()

    @patch("langchain_core.runnables.base.RunnableSequence.invoke")
    def test_generate_takeaways_with_questions(self, mocked_invoke: MagicMock):
        class MockedTakeawaysSchema:
            def __init__(self, result):
                self.result = result

            def dict(self):
                return self.result

        mocked_invoke.side_effect = [
            MockedTakeawaysSchema(
                {
                    "takeaways": [
                        {
                            "topic": "'Answer 1.1 topic'",
                            "insight": "'Answer 1.1 title'",
                            "significance": "'Answer 1.1 significance'",
                        },
                        {
                            "topic": "'Answer 1.2 topic'",
                            "insight": "'Answer 1.2 title'",
                            "significance": "'Answer 1.2 significance'",
                        },
                    ]
                }
            ),
            MockedTakeawaysSchema(
                {
                    "takeaways": [
                        {
                            "topic": "'Answer 2 topic'",
                            "insight": "'Answer 2 title'",
                            "significance": "'Answer 2 significance'",
                        },
                    ]
                }
            ),
        ]

        generate_takeaways(self.note, self.project.takeaway_types.all(), self.user)
        self.assertEqual(
            mocked_invoke.call_args_list[0].args[0],
            {
                "source": "This is a sample text only.\n\nThis is a sample text in the second block.\n\n",
            },
        )
        self.assertEqual(
            mocked_invoke.call_args_list[1].args[0],
            {
                "source": "This is a sample text only.\n\nThis is a sample text in the second block.\n\n",
            },
        )
        takeaway_titles = [takeaway.title for takeaway in self.note.takeaways.all()]
        expected_takeaway_titles = [
            "'Answer 1.1 topic' - 'Answer 1.1 title': 'Answer 1.1 significance'",
            "'Answer 1.2 topic' - 'Answer 1.2 title': 'Answer 1.2 significance'",
            "'Answer 2 topic' - 'Answer 2 title': 'Answer 2 significance'",
        ]
        self.assertCountEqual(takeaway_titles, expected_takeaway_titles)
