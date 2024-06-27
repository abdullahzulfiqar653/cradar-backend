import logging

import numpy as np
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.note import Note
from api.models.project import Project
from api.models.takeaway import Takeaway
from api.models.takeaway_type import TakeawayType
from api.models.user import User
from api.models.workspace import Workspace


class TestProjectTakeawayListView(APITestCase):
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

        # Takeaway type that is not attached to any takeaway
        self.takeaway_type3 = TakeawayType.objects.create(
            name="takeaway type 3", project=self.project
        )

        self.url = f"/api/projects/{self.project.id}/takeaway-types/"
        return super().setUp()

    def test_user_list_project_takeaway_types(self):
        expected_data = [
            {
                "id": self.takeaway_type1.id,
                "name": self.takeaway_type1.name,
                "project": self.takeaway_type1.project.id,
                "definition": "",
            },
            {
                "id": self.takeaway_type2.id,
                "name": self.takeaway_type2.name,
                "project": self.takeaway_type1.project.id,
                "definition": "",
            },
            {
                "id": self.takeaway_type3.id,
                "name": self.takeaway_type3.name,
                "project": self.takeaway_type1.project.id,
                "definition": "",
            },
        ]
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 3)
        self.assertCountEqual(response.json(), expected_data)

    def test_user_create_project_takeaway_type(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            self.url,
            {"name": "new takeaway type", "definition": "new definition"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TakeawayType.objects.filter(project=self.project).count(), 4)

    def test_user_create_project_takeaway_type_with_existing_name(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            self.url,
            {"name": self.takeaway_type1.name, "definition": "new definition"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"name": ["Takeaway type with this name already exists in this project."]},
        )
