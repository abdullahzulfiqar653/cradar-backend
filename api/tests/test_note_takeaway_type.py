import logging
from unittest.mock import patch

import numpy as np
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.note import Note
from api.models.project import Project
from api.models.takeaway import Takeaway
from api.models.takeaway_type import TakeawayType
from api.models.user import User
from api.models.workspace import Workspace


class TestNoteTakeawayTypeListCreateView(APITestCase):
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

        self.note1 = Note.objects.create(
            title="note 1", project=self.project, author=self.user
        )
        self.takeaway_type1 = TakeawayType.objects.create(
            name="takeaway type 1", project=self.project
        )
        self.takeaway1 = Takeaway.objects.create(
            title="takeaway 1",
            note=self.note1,
            created_by=self.user,
            type=self.takeaway_type1,
            vector=np.random.rand(1536),
        )

        self.note2 = Note.objects.create(
            title="note 1", project=self.project, author=self.user
        )
        self.takeaway_type2 = TakeawayType.objects.create(
            name="takeaway type 2", project=self.project
        )
        self.takeaway2 = Takeaway.objects.create(
            title="takeaway 2",
            note=self.note2,
            created_by=self.user,
            type=self.takeaway_type2,
            vector=np.random.rand(1536),
        )
        return super().setUp()

    def test_user_list_note_takeaway_types(self):
        # Test note 1
        expected_data = [
            {
                "id": self.takeaway_type1.id,
                "name": self.takeaway_type1.name,
                "project": self.takeaway_type1.project.id,
                "definition": "",
            },
        ]
        url = f"/api/reports/{self.note1.id}/takeaway-types/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.json(), expected_data)

        # Test note 2
        expected_data = [
            {
                "id": self.takeaway_type2.id,
                "name": self.takeaway_type2.name,
                "project": self.takeaway_type1.project.id,
                "definition": "",
            },
        ]
        url = f"/api/reports/{self.note2.id}/takeaway-types/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.json(), expected_data)

    @patch("api.tasks.analyze_existing_note.delay")
    def test_user_create_note_takeaway_type(self, mocked_delay):
        url = f"/api/reports/{self.note1.id}/takeaway-types/"
        data = {"takeaway_type_ids": [self.takeaway_type1.id, self.takeaway_type2.id]}
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mocked_delay.assert_called_once_with(
            self.note1.id,
            [self.takeaway_type1.id, self.takeaway_type2.id],
            self.user.id,
        )

    def test_user_create_note_takeaway_type_with_only_invalid_takeaway_type(self):
        url = f"/api/reports/{self.note1.id}/takeaway-types/"
        data = {"takeaway_type_ids": ["invalid_id"]}
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_outsider_list_project_takeaway_types(self):
        url = f"/api/reports/{self.note1.id}/takeaway-types/"
        self.client.force_authenticate(self.outsider)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
