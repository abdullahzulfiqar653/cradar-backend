import logging

import numpy as np
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.highlight import Highlight
from api.models.keyword import Keyword
from api.models.note import Note, blank_content
from api.models.note_type import NoteType
from api.models.organization import Organization
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


# Create your tests here.
class TestNoteKeywordDestroyView(APITestCase):
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
        self.existing_keyword = Keyword.objects.create(name="keyword")
        self.note.keywords.add(self.existing_keyword)
        return super().setUp()

    def test_user_delete_insight_takeaways(self):
        self.client.force_authenticate(self.user)
        keyword_id = self.existing_keyword.id
        url = f"/api/reports/{self.note.id}/keywords/{keyword_id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(self.note.keywords.contains(self.existing_keyword))

    def test_user_delete_nonexisting_insight_takeaways(self):
        self.client.force_authenticate(self.user)
        non_existing_keyword_id = "nonexistenceid"
        url = f"/api/reports/{self.note.id}/keywords/{non_existing_keyword_id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_delete_insight_takeaways(self):
        self.client.force_authenticate(self.outsider)
        keyword_id = self.existing_keyword.id
        url = f"/api/reports/{self.note.id}/keywords/{keyword_id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(self.note.keywords.contains(self.existing_keyword))


class TestNoteRetrieveUpdateDeleteView(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="user", password="password")
        self.outsider = User.objects.create_user(
            username="outsider", password="password"
        )

        workspace = Workspace.objects.create(name="workspace", owned_by=self.user)
        workspace.members.add(self.user, through_defaults={"role": "Editor"})
        self.project = Project.objects.create(name="project", workspace=workspace)
        self.project.users.add(self.user)

        self.note_type1 = NoteType.objects.create(
            name="Report-type-1", project=self.project, vector=np.random.rand(1536)
        )
        self.note_type2 = NoteType.objects.create(
            name="Report-type-2", project=self.project, vector=np.random.rand(1536)
        )

        self.note = Note.objects.create(
            title="note",
            project=self.project,
            author=self.user,
        )
        self.single_line_highlight = Highlight.objects.create(
            title="sample",
            note=self.note,
            created_by=self.user,
            vector=np.random.rand(1536),
        )
        self.multiline_highlight = Highlight.objects.create(
            title="only.This",
            note=self.note,
            created_by=self.user,
            vector=np.random.rand(1536),
        )
        self.note.content = {
            "root": {
                "children": [
                    {
                        "children": [
                            {
                                "text": "This is a ",
                                "type": "text",
                            },
                            {
                                "type": "mark",
                                "ids": [self.single_line_highlight.id],
                                "children": [
                                    {
                                        "text": "sample",
                                        "type": "text",
                                    }
                                ],
                            },
                            {
                                "text": " text only.",
                                "type": "text",
                            },
                            {
                                "type": "mark",
                                "ids": [self.multiline_highlight.id],
                                "children": [
                                    {
                                        "text": "only.",
                                        "type": "text",
                                    }
                                ],
                            },
                        ],
                        "type": "paragraph",
                    },
                    {
                        "children": [
                            {
                                "type": "mark",
                                "ids": [self.multiline_highlight.id],
                                "children": [
                                    {
                                        "text": "This",
                                        "type": "text",
                                    }
                                ],
                            },
                            {
                                "text": " is a sample text in the second block.",
                                "type": "text",
                            },
                        ],
                        "type": "paragraph",
                    },
                ],
                "type": "root",
            }
        }

        self.highlight_count = 2
        self.note.save()
        return super().setUp()

    def test_create_single_line_highlight(self):
        self.client.force_authenticate(self.user)
        url = f"/api/reports/{self.note.id}/"
        content = self.note.content
        # Add a new highlight "text" from the second block.
        paragraph = content["root"]["children"][0]
        paragraph["children"][2:3] = [
            {
                "text": " ",
                "type": "text",
            },
            {
                "type": "mark",
                "ids": [None],
                "children": [
                    {
                        "text": "text",
                        "type": "text",
                    }
                ],
            },
            {
                "text": " only.",
                "type": "text",
            },
        ]
        data = {"content": content}
        response = self.client.patch(url, data=data)
        self.note.refresh_from_db()
        self.assertEqual(self.note.highlights.count(), self.highlight_count + 1)
        last_created_highlight = self.note.highlights.order_by("created_at").last()
        self.assertEqual(last_created_highlight.title, "text")

    def test_create_multiline_highlight(self):
        self.client.force_authenticate(self.user)
        url = f"/api/reports/{self.note.id}/"
        content = self.note.content
        # Add a new highlight "text" that spans the first and second block.
        content["root"]["children"][0]["children"][3]["ids"].append(None)
        content["root"]["children"][1]["children"][0]["ids"].append(None)
        data = {"content": content}
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.note.refresh_from_db()
        self.assertEqual(self.note.highlights.count(), self.highlight_count + 1)
        last_created_highlight = self.note.highlights.order_by("created_at").last()
        self.assertTrue(last_created_highlight.title, "only.This")

    def test_remove_content(self):
        self.client.force_authenticate(self.user)
        url = f"/api/reports/{self.note.id}/"
        data = {"content": blank_content()}
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.note.refresh_from_db()
        self.assertEqual(self.note.highlights.count(), 0)

    def test_remove_all_highlights_with_content(self):
        self.client.force_authenticate(self.user)
        url = f"/api/reports/{self.note.id}/"
        data = {
            "content": {
                "root": {
                    "type": "root",
                    "children": [
                        {
                            "type": "paragraph",
                            "text": "This is a text with no highlights.",
                        }
                    ],
                }
            }
        }
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.note.refresh_from_db()
        self.assertEqual(self.note.highlights.count(), 0)

    def test_user_update_note_organization(self):
        self.client.force_authenticate(self.user)
        url = f"/api/reports/{self.note.id}/"

        # Test add organization
        data = {"organizations": [{"name": "added organization"}]}
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.note.organizations.count(), 1)
        organization1 = self.note.organizations.first()
        self.assertEqual(organization1.name, "added organization")

        # Test replace organization
        data = {"organizations": [{"name": "replaced organization"}]}
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.note.organizations.count(), 1)
        organization2 = self.note.organizations.first()
        self.assertEqual(organization2.name, "replaced organization")
        self.assertEqual(
            Organization.objects.filter(id=organization1.id).count(),
            0,
            "Organization that is not related to any note is not cleaned up.",
        )

    def test_user_update_note_type(self):
        self.client.force_authenticate(self.user)
        url = f"/api/reports/{self.note.id}/"

        # Test add type
        data = {"type_id": self.note_type1.id}
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.note.refresh_from_db()
        self.assertEqual(self.note.type.id, self.note_type1.id)

        # Test replace type
        data = {"type_id": self.note_type2.id}
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.note.refresh_from_db()
        self.assertEqual(self.note.type.id, self.note_type2.id)

    def test_outsider_retrieve_note(self):
        self.client.force_authenticate(self.outsider)
        url = f"/api/reports/{self.note.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
