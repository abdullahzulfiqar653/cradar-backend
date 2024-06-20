import logging

import numpy as np
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.note import Note
from api.models.note_type import NoteType
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class TestProjectTypeListView(APITestCase):
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

        self.note_type1 = NoteType.objects.create(
            name="Report-type-1", project=self.project, vector=np.random.rand(1536)
        )
        self.note_type2 = NoteType.objects.create(
            name="Report-type-2", project=self.project, vector=np.random.rand(1536)
        )

        self.url = f"/api/projects/{self.project.id}/report-types/"
        return super().setUp()

    def test_user_list_report_types_in_project(self):
        Note.objects.create(
            title="Sample report",
            project=self.project,
            author=self.user,
            type=self.note_type1,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_results = [
            {
                "id": self.note_type1.id,
                "name": self.note_type1.name,
                "project": self.project.id,
                "report_count": 1,
            },
            {
                "id": self.note_type2.id,
                "name": self.note_type2.name,
                "project": self.project.id,
                "report_count": 0,
            },
        ]
        self.assertEqual(response.json(), expected_results)

    def test_user_list_report_types_in_project_with_search(self):
        Note.objects.create(
            title="Sample report",
            project=self.project,
            author=self.user,
            type=self.note_type1,
        )
        Note.objects.create(
            title="Sample report with a different type",
            project=self.project,
            author=self.user,
            type=self.note_type2,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(f"{self.url}?search=Report-type-1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_results = [
            {
                "id": self.note_type1.id,
                "name": self.note_type1.name,
                "project": self.project.id,
                "report_count": 1,
            }
        ]
        self.assertEqual(response.json(), expected_results)

    def test_user_create_report_type_in_project(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={"name": "New Report type"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NoteType.objects.count(), 3)

    def test_user_create_report_type_in_project_with_existing_name(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={"name": self.note_type1.name})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"name": ["Report type with this name already exists in this project."]},
        )
