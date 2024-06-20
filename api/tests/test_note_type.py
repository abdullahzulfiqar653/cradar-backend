import logging

import numpy as np
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.note_type import NoteType
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class TestNoteTypeRetrieveUpdateDestroyView(APITestCase):
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
        return super().setUp()

    def test_user_retrieve_report_type(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(f"/api/report-types/{self.note_type1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_result = {
            "id": self.note_type1.id,
            "name": self.note_type1.name,
            "project": self.project.id,
        }
        self.assertEqual(response.data, expected_result)

    def test_user_update_report_type(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            f"/api/report-types/{self.note_type1.id}/",
            {"name": "Updated name"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        original_vector = np.array(self.note_type1.vector)

        self.note_type1.refresh_from_db()
        self.assertEqual(self.note_type1.name, "Updated name")

        # Check that the vector is updated
        current_vector = np.array(self.note_type1.vector)
        self.assertFalse(np.array_equal(original_vector, current_vector))

    def test_user_update_report_type_with_existing_name(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            f"/api/report-types/{self.note_type1.id}/",
            {"name": self.note_type2.name},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"name": ["Report type with this name already exists in this project."]},
        )

    def test_user_update_report_type_project(self):
        new_workspace = Workspace.objects.create(
            name="new_workspace", owned_by=self.user
        )
        new_workspace.members.add(self.user, through_defaults={"role": "Editor"})
        new_project = Project.objects.create(
            name="new_project", workspace=new_workspace
        )
        new_project.users.add(self.user)

        self.client.force_authenticate(self.user)
        response = self.client.patch(
            f"/api/report-types/{self.note_type1.id}/",
            {"project": new_project.id},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that the project is not updated
        self.note_type1.refresh_from_db()
        self.assertEqual(self.note_type1.project, self.project)

    def test_user_delete_report_type(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(f"/api/report-types/{self.note_type1.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(NoteType.objects.filter(id=self.note_type1.id).exists())

    def test_user_delete_last_report_type(self):
        self.note_type1.delete()
        self.client.force_authenticate(self.user)
        response = self.client.delete(f"/api/report-types/{self.note_type2.id}/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(NoteType.objects.filter(id=self.note_type2.id).exists())
        self.assertEqual(
            response.data, {"detail": "The report type list must not be empty."}
        )

    def test_outsider_retrieve_report_type(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.get(f"/api/report-types/{self.note_type1.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_update_report_type(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.patch(
            f"/api/report-types/{self.note_type1.id}/",
            {"name": "Updated name"},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
