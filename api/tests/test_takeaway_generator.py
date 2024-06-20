import logging
from unittest.mock import MagicMock, patch

import numpy as np
from rest_framework.test import APITestCase

from api.ai.generators.takeaway_generator_default_question import (
    generate_takeaways_default_question,
)
from api.ai.generators.takeaway_generator_with_questions import (
    generate_takeaways_with_questions,
)
from api.models.note import Note
from api.models.note_type import NoteType
from api.models.project import Project
from api.models.question import Question
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
        self.question1 = Question.objects.create(
            title="Test question 1", project=self.project
        )
        self.question2 = Question.objects.create(
            title="Test question 2", project=self.project
        )
        self.note.questions.add(self.question1, self.question2)
        return super().setUp()

    @patch("langchain_core.runnables.base.RunnableSequence.invoke")
    def test_generate_takeaways_default_question(self, mocked_invoke: MagicMock):
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
                            "type": "Answer 1.1 type",
                        },
                        {
                            "topic": "'Answer 1.2 topic'",
                            "insight": "'Answer 1.2 title'",
                            "significance": "'Answer 1.2 significance'",
                            "type": "Answer 1.2 type",
                        },
                    ]
                }
            ),
        ]

        generate_takeaways_default_question(self.note, self.user)
        self.assertEqual(
            mocked_invoke.call_args_list[0].args[0],
            {
                "text": "This is a sample text only.\n\nThis is a sample text in the second block.\n\n",
            },
        )
        takeaway_titles = [takeaway.title for takeaway in self.note.takeaways.all()]
        expected_takeaway_titles = [
            "'Answer 1.1 topic' - 'Answer 1.1 title': 'Answer 1.1 significance'",
            "'Answer 1.2 topic' - 'Answer 1.2 title': 'Answer 1.2 significance'",
        ]
        self.assertCountEqual(takeaway_titles, expected_takeaway_titles)

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
                            "type": "Answer 1.1 type",
                        },
                        {
                            "topic": "'Answer 1.2 topic'",
                            "insight": "'Answer 1.2 title'",
                            "significance": "'Answer 1.2 significance'",
                            "type": "Answer 1.2 type",
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
                            "type": "Answer 2 type",
                        },
                    ]
                }
            ),
        ]

        generate_takeaways_with_questions(
            self.note, self.note.questions.all(), self.user
        )
        self.assertEqual(
            mocked_invoke.call_args_list[0].args[0],
            {
                "text": "This is a sample text only.\n\nThis is a sample text in the second block.\n\n",
                "question": "Test question 1",
            },
        )
        self.assertEqual(
            mocked_invoke.call_args_list[1].args[0],
            {
                "text": "This is a sample text only.\n\nThis is a sample text in the second block.\n\n",
                "question": "Test question 2",
            },
        )
        takeaway_titles = [takeaway.title for takeaway in self.note.takeaways.all()]
        expected_takeaway_titles = [
            "'Answer 1.1 topic' - 'Answer 1.1 title': 'Answer 1.1 significance'",
            "'Answer 1.2 topic' - 'Answer 1.2 title': 'Answer 1.2 significance'",
            "'Answer 2 topic' - 'Answer 2 title': 'Answer 2 significance'",
        ]
        self.assertCountEqual(takeaway_titles, expected_takeaway_titles)
