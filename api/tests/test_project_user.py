import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace
from api.models.workspace_user import WorkspaceUser


class TestProjectUserListView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.workspace_owner = User.objects.create_user(
            username="workspace_owner@example.com",
            email="workspace_owner@example.com",
            password="password",
        )
        self.workspace_member = User.objects.create_user(
            username="workspace_member@example.com",
            email="workspace_member@example.com",
            password="password",
        )
        self.outsider = User.objects.create_user(
            username="outsider", password="password"
        )

        workspace = Workspace.objects.create(
            name="workspace", owned_by=self.workspace_owner
        )
        workspace.members.add(self.workspace_owner, through_defaults={"role": "Owner"})
        workspace.members.add(self.workspace_member)
        self.project = Project.objects.create(name="project", workspace=workspace)
        self.project.users.add(self.workspace_owner)
        self.project.users.add(self.workspace_member)
        return super().setUp()

    def test_workspace_owner_list_project_users(self):
        self.client.force_authenticate(self.workspace_owner)
        url = f"/api/projects/{self.project.id}/users/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [
            {
                "email": "workspace_owner@example.com",
                "first_name": "",
                "last_name": "",
                "role": WorkspaceUser.Role.OWNER,
            },
            {
                "email": "workspace_member@example.com",
                "first_name": "",
                "last_name": "",
                "role": WorkspaceUser.Role.VIEWER,
            },
        ]
        self.assertCountEqual(response.json(), expected_data)

    def test_outsider_list_project_users(self):
        self.client.force_authenticate(self.outsider)
        url = f"/api/projects/{self.project.id}/users/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
