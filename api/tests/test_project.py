import logging

from rest_framework.test import APITestCase

from api.models.note import Note
from api.models.project import Project
from api.models.usage.token import TokenUsage
from api.models.usage.transciption import TranscriptionUsage
from api.models.user import User
from api.models.workspace import Workspace


class TestProjectRetrieveUpdateDeleteView(APITestCase):
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
        self.project = Project.objects.create(name="project", workspace=workspace)
        self.project.users.add(self.user)
        self.url = f"/api/projects/{self.project.id}/"
        return super().setUp()

    def test_user_retrieve_project_has_usage(self):
        """
        Test if the usage data exists in the endpoint response payload.
        """
        note = Note.objects.create(
            title="note",
            project=self.project,
            author=self.user,
            file_size=1000,
        )
        TokenUsage.objects.create(
            workspace=self.project.workspace,
            project=self.project,
            content_object=note,
            action="test-usage",
            created_by=self.user,
            value=150,
            cost=0.0001,
        )
        TranscriptionUsage.objects.create(
            workspace=self.project.workspace,
            project=self.project,
            note=note,
            created_by=self.user,
            value=118,
            cost=0.0001,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        workspace_data = response.json()["workspace"]
        expected_usage_data = {
            "usage_minutes": 2,
            "usage_tokens": 150,
            "total_file_size": 1000,
        }
        self.assertDictContainsSubset(expected_usage_data, workspace_data)

    def test_user_retrieve_project_usage_calculation_multiple_notes(self):
        """
        Test usage calculation sum usage minutes and usage tokens
        over multiple notes properly.
        """
        note1 = Note.objects.create(
            title="note",
            project=self.project,
            author=self.user,
            file_size=500,
        )
        note2 = Note.objects.create(
            title="note",
            project=self.project,
            author=self.user,
            file_size=1000,
        )
        TokenUsage.objects.create(
            workspace=self.project.workspace,
            project=self.project,
            content_object=note1,
            action="test-usage",
            created_by=self.user,
            value=150,
            cost=0.0001,
        )
        TokenUsage.objects.create(
            workspace=self.project.workspace,
            project=self.project,
            content_object=note2,
            action="test-usage",
            created_by=self.user,
            value=542,
            cost=0.0001,
        )
        TranscriptionUsage.objects.create(
            workspace=self.project.workspace,
            project=self.project,
            note=note1,
            created_by=self.user,
            value=118,
            cost=0.0001,
        )
        TranscriptionUsage.objects.create(
            workspace=self.project.workspace,
            project=self.project,
            note=note1,
            created_by=self.user,
            value=435,
            cost=0.0001,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        workspace_data = response.json()["workspace"]
        expected_usage_minutes = round((118 + 435) / 60.0)
        expected_usage_tokens = 150 + 542
        expected_total_file_size = 500 + 1000
        expected_usage_data = {
            "usage_minutes": expected_usage_minutes,
            "usage_tokens": expected_usage_tokens,
            "total_file_size": expected_total_file_size,
        }
        self.assertDictContainsSubset(expected_usage_data, workspace_data)

    def test_user_retrieve_project_usage_calculation_multiple_projects(self):
        """
        Test usage calculation can handle notes in multiple projects.
        """
        note1 = Note.objects.create(
            title="note",
            project=self.project,
            author=self.user,
            file_size=500,
        )
        another_project = Project.objects.create(
            name="project", workspace=self.project.workspace
        )
        note2 = Note.objects.create(
            title="note",
            project=another_project,
            author=self.user,
            file_size=1000,
        )
        TokenUsage.objects.create(
            workspace=self.project.workspace,
            project=self.project,
            content_object=note1,
            action="test-usage",
            created_by=self.user,
            value=150,
            cost=0.0001,
        )
        TokenUsage.objects.create(
            workspace=self.project.workspace,
            project=another_project,
            content_object=note2,
            action="test-usage",
            created_by=self.user,
            value=542,
            cost=0.0001,
        )
        TranscriptionUsage.objects.create(
            workspace=self.project.workspace,
            project=self.project,
            note=note1,
            created_by=self.user,
            value=118,
            cost=0.0001,
        )
        TranscriptionUsage.objects.create(
            workspace=self.project.workspace,
            project=another_project,
            note=note2,
            created_by=self.user,
            value=435,
            cost=0.0001,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        workspace_data = response.json()["workspace"]
        expected_usage_minutes = round((118 + 435) / 60.0)
        expected_usage_tokens = 150 + 542
        expected_total_file_size = 500 + 1000
        expected_usage_data = {
            "usage_minutes": expected_usage_minutes,
            "usage_tokens": expected_usage_tokens,
            "total_file_size": expected_total_file_size,
        }
        self.assertDictContainsSubset(expected_usage_data, workspace_data)
