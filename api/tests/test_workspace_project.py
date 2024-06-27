import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.note_type import default_note_types
from api.models.project import Project
from api.models.takeaway_type import default_takeaway_types
from api.models.user import User
from api.models.workspace import Workspace
from api.models.workspace_user import WorkspaceUser


class TestWorkspaceProjectListCreateView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.owner = User.objects.create_user(
            username="owner@example.com",
            email="owner@example.com",
            password="password",
        )
        self.workspace = Workspace.objects.create(name="workspace", owned_by=self.owner)
        self.workspace.members.add(
            self.owner, through_defaults={"role": WorkspaceUser.Role.OWNER}
        )

        self.editor = User.objects.create_user(
            username="editor@example.com",
            email="editor@example.com",
            password="password",
        )
        self.workspace.members.add(
            self.editor, through_defaults={"role": WorkspaceUser.Role.EDITOR}
        )

        self.viewer = User.objects.create_user(
            username="viewer@example.com",
            email="viewer@example.com",
            password="password",
        )
        self.workspace.members.add(
            self.viewer, through_defaults={"role": WorkspaceUser.Role.VIEWER}
        )
        self.project = Project.objects.create(name="project", workspace=self.workspace)
        self.project.users.add(self.editor)

    def test_editor_list_workspace_project(self):
        self.client.force_authenticate(self.editor)
        response = self.client.get(f"/api/workspaces/{self.workspace.id}/projects/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [
            {
                "id": str(self.project.id),
                "name": self.project.name,
                "description": "",
                "workspace": {
                    "id": str(self.workspace.id),
                    "name": self.workspace.name,
                    "is_owner": False,
                },
                "language": "en",
            }
        ]
        self.assertEqual(response.data, expected_data)

    def test_editor_create_workspace_project(self):
        self.client.force_authenticate(self.editor)
        response = self.client.post(
            f"/api/workspaces/{self.workspace.id}/projects/",
            {"name": "new project"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.workspace.projects.count(), 2)

        project_id = response.data["id"]
        project = self.workspace.projects.get(id=project_id)

        # Check if default note types are created
        self.assertCountEqual(
            project.note_types.values_list("name", flat=True),
            default_note_types,
        )

        # Check if default takeaway types are created
        self.assertCountEqual(
            project.takeaway_types.values("name", "definition"),
            default_takeaway_types,
        )
