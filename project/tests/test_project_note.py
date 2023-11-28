import logging

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from note.models import Note
from project.models import Project
from workspace.models import Workspace


class TestProjectNoteListCreateView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(username="user", password="password")
        self.outsider = User.objects.create_user(
            username="outsider", password="password"
        )

        workspace = Workspace.objects.create(name="workspace")
        self.project = Project.objects.create(name="project", workspace=workspace)
        self.project.users.add(self.user)
        self.url = f"/api/projects/{self.project.id}/reports/"
        return super().setUp()

    def test_user_list_report_filter_type(self):
        Note.objects.create(
            title="Sample report",
            project=self.project,
            author=self.user,
            type="Report-type-1",
        )
        Note.objects.create(
            title="Sample report with the same type",
            project=self.project,
            author=self.user,
            type="Report-type-1",
        )
        Note.objects.create(
            title="Sample report with a different type",
            project=self.project,
            author=self.user,
            type="Report-type-2",
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(f"{self.url}?type=Report-type-1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_user_create_report_exceed_usage_minutes(self):
        Note.objects.create(
            title="Use up all usage minutes.",
            project=self.project,
            author=self.user,
            file_duration_seconds=61 * 60,
        )
        data = {
            "title": "Attempt to add one more report",
            "company_name": "Test company",
        }
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_create_report_exceed_usage_tokens(self):
        Note.objects.create(
            title="Use up all usage minutes.",
            project=self.project,
            author=self.user,
            analyzing_tokens=51_000,
        )
        data = {
            "title": "Attempt to add one more report",
            "company_name": "Test company",
        }
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Assert that the endpoint doesn't create the note.
        self.assertEqual(self.project.notes.count(), 1)