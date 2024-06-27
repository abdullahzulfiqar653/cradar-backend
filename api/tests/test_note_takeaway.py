import logging

import numpy as np
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.note import Note
from api.models.project import Project
from api.models.tag import Tag
from api.models.takeaway import Takeaway
from api.models.user import User
from api.models.workspace import Workspace


class TestNoteTakeawayListCreateView(APITestCase):
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

        self.takeaway_type1 = self.project.takeaway_types.create(name="type 1")
        self.takeaway_type2 = self.project.takeaway_types.create(name="type 2")

        self.note = Note.objects.create(
            title="note 1", project=self.project, author=self.user
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
        self.tag = Tag.objects.create(name="tag", project=self.project)
        self.takeaway1.tags.add(self.tag)

        self.url = f"/api/reports/{self.note.id}/takeaways/"
        return super().setUp()

    def test_user_list_report_takeaways(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_user_list_report_takeaways_filter_tag(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(f"{self.url}?tag={self.tag.name}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_user_create_takeaway(self):
        data = {
            "title": "takeaway title",
            "type_id": self.takeaway_type1.id,
            "priority": "Low",
        }
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        takeaway_id = response.json()["id"]
        takeaway = Takeaway.objects.get(id=takeaway_id)
        self.assertEqual(takeaway.title, "takeaway title")
        self.assertEqual(takeaway.type, self.takeaway_type1)
        self.assertEqual(takeaway.priority, "Low")

    def test_user_create_takeaway_with_null_type(self):
        data = {
            "title": "takeaway title",
            "type": None,
            "priority": "Low",
        }
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        takeaway_id = response.json()["id"]
        takeaway = Takeaway.objects.get(id=takeaway_id)
        self.assertEqual(takeaway.title, "takeaway title")
        self.assertIsNone(takeaway.type)
        self.assertEqual(takeaway.priority, "Low")
