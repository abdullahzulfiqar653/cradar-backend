import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.note_template import NoteTemplate
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


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

        workspace = Workspace.objects.create(name="workspace", owned_by=self.user)
        self.project = Project.objects.create(name="project", workspace=workspace)
        self.project.users.add(self.user)
        self.outsider_project = Project.objects.create(
            name="outsider project", workspace=workspace
        )
        self.outsider_project.users.add(self.outsider)

        self.public_note_template = NoteTemplate.objects.create(
            title="public note template"
        )

        self.project_note_template = NoteTemplate.objects.create(
            title="project note template", project=self.project
        )
        return super().setUp()

    def test_user_list_note_template(self):
        "List both public and project note templates"
        url = f"/api/projects/{self.project.id}/report-templates/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response = [
            {
                "id": self.public_note_template.id,
                "title": self.public_note_template.title,
                "description": self.public_note_template.description,
                "project": None,
            },
            {
                "id": self.project_note_template.id,
                "title": self.project_note_template.title,
                "description": self.project_note_template.description,
                "project": self.project.id,
            },
        ]
        self.assertCountEqual(response.json(), expected_response)

    def test_user_create_note_template(self):
        url = f"/api/projects/{self.project.id}/report-templates/"
        self.client.force_authenticate(self.user)
        data = {
            "title": "note template title",
            "description": "note template description",
            "questions": [
                {"title": "question 1"},
                {"title": "question 2"},
            ],
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        note_template_id = response.json()["id"]
        note_template = NoteTemplate.objects.get(id=note_template_id)
        self.assertEqual(note_template.title, "note template title")
        self.assertEqual(note_template.description, "note template description")
        self.assertEqual(note_template.project, self.project)
        self.assertEqual(
            list(note_template.questions.values("title", "project")),
            [
                {"title": "question 1", "project": self.project.id},
                {"title": "question 2", "project": self.project.id},
            ],
        )

    def test_user_create_public_note_template(self):
        "Test user cannot create a public note templates by not supplying project id"
        url = f"/api/projects//report-templates/"
        self.client.force_authenticate(self.user)
        data = {
            "title": "note template title",
            "description": "note template description",
            "questions": [
                {"title": "question 1"},
                {"title": "question 2"},
            ],
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_list_note_template(self):
        "List only public note templates (outsider project doesn't have note templates)"
        url = f"/api/projects/{self.outsider_project.id}/report-templates/"
        self.client.force_authenticate(self.outsider)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response = [
            {
                "id": self.public_note_template.id,
                "title": self.public_note_template.title,
                "description": self.public_note_template.description,
                "project": None,
            },
        ]
        self.assertCountEqual(response.json(), expected_response)
