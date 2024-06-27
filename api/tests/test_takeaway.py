import logging

import numpy as np
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.highlight import Highlight
from api.models.note import Note
from api.models.project import Project
from api.models.tag import Tag
from api.models.takeaway import Takeaway
from api.models.user import User
from api.models.workspace import Workspace


class TestTakeawayRetrieveUpdateDeleteView(APITestCase):
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

        self.takeaway_type = self.project.takeaway_types.create(name="takeaway type")
        self.highlight = Highlight.objects.create(
            title="highlight",
            note=self.note,
            created_by=self.user,
            type=self.takeaway_type,
            vector=np.random.rand(1536),
        )
        self.takeaway = self.highlight.takeaway_ptr
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
                                "ids": [self.highlight.id],
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
                        ],
                        "type": "paragraph",
                    },
                ],
                "type": "root",
            }
        }
        self.note.save()

        self.tag = Tag.objects.create(name="tag", project=self.project)
        self.takeaway.tags.add(self.tag)

        return super().setUp()

    def test_outsider_retrieve_takeaway(self):
        url = f"/api/takeaways/{self.takeaway.id}/"
        self.client.force_authenticate(self.outsider)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_retrieve_takeaway(self):
        url = f"/api/takeaways/{self.takeaway.id}/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("priority", response.json())

    def test_user_update_takeaway_type(self):
        url = f"/api/takeaways/{self.takeaway.id}/"
        data = {
            "type_id": None,
        }
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.takeaway.refresh_from_db()
        self.assertIsNone(self.takeaway.type)

    def test_user_update_takeaway_priority(self):
        url = f"/api/takeaways/{self.takeaway.id}/"
        data = {
            "priority": Takeaway.Priority.HIGH,
        }
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.takeaway.refresh_from_db()
        self.assertEqual(self.takeaway.type, self.takeaway_type)
        self.assertEqual(self.takeaway.priority, Takeaway.Priority.HIGH)

    def test_user_delete_takeaway(self):
        self.assertTrue(Takeaway.objects.filter(id=self.takeaway.id).exists())
        url = f"/api/takeaways/{self.takeaway.id}/"
        self.client.force_authenticate(self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Takeaway.objects.filter(id=self.takeaway.id).exists())

        # Make sure that the highlight is removed from the note.content
        self.note.refresh_from_db()
        stack = [self.note.content["root"]]
        while stack:
            node = stack.pop()
            self.assertNotEqual(node.get("type"), "mark")
            stack.extend(node.get("children", []))

        # Make sure that the tags are cleaned up
        self.assertFalse(Tag.objects.filter(id=self.tag.id).exists())
