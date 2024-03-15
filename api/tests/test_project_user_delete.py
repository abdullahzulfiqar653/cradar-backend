import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class TestProjectNoteListCreateView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.workspace_owner = User.objects.create_user(
            username="workspace_owner@example.com", password="password"
        )
        self.workspace_member = User.objects.create_user(
            username="workspace_member@example.com", password="password"
        )
        self.outsider = User.objects.create_user(
            username="outsider", password="password"
        )

        workspace = Workspace.objects.create(
            name="workspace", owned_by=self.workspace_owner
        )
        self.project = Project.objects.create(name="project", workspace=workspace)
        self.project.users.add(self.workspace_owner)
        self.project.users.add(self.workspace_member)
        return super().setUp()

    def test_workspace_owner_delete_workspace_member(self):
        self.client.force_authenticate(self.workspace_owner)
        url = f"/api/projects/{self.project.id}/users/delete/"
        data = {
            "users": [
                {"username": self.workspace_member.username},
                {"username": "something_else@example.com"},
            ],
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            response.json(), {"users": [{"username": "workspace_member@example.com"}]}
        )
        self.assertCountEqual(self.project.users.all(), [self.workspace_owner])

    def test_workspace_member_delete_workspace_owner(self):
        self.client.force_authenticate(self.workspace_member)
        url = f"/api/projects/{self.project.id}/users/delete/"
        data = {
            "users": [
                {"username": self.workspace_owner.username},
            ],
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_delete_workspace_member(self):
        self.client.force_authenticate(self.outsider)
        url = f"/api/projects/{self.project.id}/users/delete/"
        data = {
            "users": [
                {"username": self.workspace_member.username},
            ],
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
