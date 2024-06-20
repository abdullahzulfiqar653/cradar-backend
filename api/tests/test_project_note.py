import json
import logging
import tempfile
import unittest
from unittest.mock import Mock, patch

import numpy as np
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.keyword import Keyword
from api.models.note import Note
from api.models.note_type import NoteType
from api.models.project import Project
from api.models.usage.transciption import TranscriptionUsage
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

    def test_user_list_report_filter_report_type(self):
        Note.objects.create(
            title="Sample report",
            project=self.project,
            author=self.user,
            type=self.note_type1,
        )
        Note.objects.create(
            title="Sample report with the same type",
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
        url = f"/api/projects/{self.project.id}/reports/?type=Report-type-1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
        for report in response.json():
            self.assertEqual(report["type"]["id"], self.note_type1.id)

    def test_user_list_report_filter_keyword(self):
        note_with_keyword = Note.objects.create(
            title="Report with keyword",
            project=self.project,
            author=self.user,
        )
        keyword = Keyword.objects.create(name="keyword")
        note_with_keyword.keywords.add(keyword)

        Note.objects.create(
            title="Report without keyword",
            project=self.project,
            author=self.user,
        )

        self.client.force_authenticate(self.user)
        url = f"/api/projects/{self.project.id}/reports/?keyword=keyword"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], note_with_keyword.id)

    def test_user_list_report_search(self):
        Note.objects.create(
            title="Sample report",
            project=self.project,
            author=self.user,
            type=self.note_type1,
        )
        Note.objects.create(
            title="Sample report with search term",
            project=self.project,
            author=self.user,
            type=self.note_type1,
        )
        Note.objects.create(
            title="Another sample report with search term",
            project=self.project,
            author=self.user,
            type=self.note_type2,
        )
        self.client.force_authenticate(self.user)
        url = f"/api/projects/{self.project.id}/reports/?search=search%20term"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_user_create_report(self):
        data = {
            "title": "User can create report.",
            "organizations": [
                {
                    "name": "Test company",
                }
            ],
            "keywords": [
                {
                    "name": "Keyword 1",
                },
                {
                    "name": "Keyword 2",
                },
            ],
        }
        self.client.force_authenticate(self.user)
        url = f"/api/projects/{self.project.id}/reports/"
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Check that organization is created
        response_json = response.json()
        note = Note.objects.get(id=response_json["id"])
        self.assertEqual(note.organizations.count(), 1)
        self.assertEqual(note.keywords.count(), 2)

    def test_user_create_report_with_long_title(self):
        data = {
            "title": "Long title: " + "x" * 255,
            "organizations": [
                {
                    "name": "Test company",
                }
            ],
        }
        self.client.force_authenticate(self.user)
        url = f"/api/projects/{self.project.id}/reports/"
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_create_report_with_more_than_8_questions(self):
        data = {
            "title": "User can create report.",
            "questions": [
                {"title": "question 1"},
                {"title": "question 2"},
                {"title": "question 3"},
                {"title": "question 4"},
                {"title": "question 5"},
                {"title": "question 6"},
                {"title": "question 7"},
                {"title": "question 8"},
                {"title": "question 9"},
            ],
        }
        self.client.force_authenticate(self.user)
        url = f"/api/projects/{self.project.id}/reports/"
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("api.tasks.analyze_new_note.delay")
    def test_user_create_report_with_file(self, mocked_analyze: Mock):
        data = {
            "title": "User can create report.",
            "organizations": [
                {
                    "name": "Test company",
                }
            ],
        }
        with (
            tempfile.NamedTemporaryFile("r+", suffix=".txt") as file,
            tempfile.NamedTemporaryFile("r+", suffix=".json") as data_file,
        ):
            file.write("File content.")
            file.seek(0)

            json.dump(data, data_file)
            data_file.seek(0)

            self.client.force_authenticate(self.user)
            url = f"/api/projects/{self.project.id}/reports/"
            payload = {"file": file, "data": data_file}
            response = self.client.post(url, data=payload, format="multipart")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            mocked_analyze.assert_called_once()

    @patch("api.tasks.analyze_new_note.delay")
    def test_user_create_report_with_url(self, mocked_analyze: Mock):
        data = {
            "title": "User can create report.",
            "url": "www.example.com",
            "organizations": [
                {
                    "name": "Test company",
                }
            ],
        }
        self.client.force_authenticate(self.user)
        url = f"/api/projects/{self.project.id}/reports/"
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mocked_analyze.assert_called_once()

    def test_user_create_report_exceed_usage_minutes(self):
        note = Note.objects.create(
            title="Use up all usage minutes.",
            project=self.project,
            author=self.user,
        )
        TranscriptionUsage.objects.create(
            workspace=self.project.workspace,
            project=self.project,
            note=note,
            created_by=self.user,
            value=10 * 60 * 60,
            cost=0.0001,
        )

        data = {
            "title": "Attempt to add one more report",
            "organizations": [
                {
                    "name": "Test company",
                }
            ],
        }
        with (
            open("api/tests/files/sample-3s.mp3", "rb") as file,
            tempfile.NamedTemporaryFile("r+", suffix=".json") as data_file,
        ):
            json.dump(data, data_file)
            data_file.seek(0)

            self.client.force_authenticate(self.user)
            url = f"/api/projects/{self.project.id}/reports/"
            payload = {"file": file, "data": data_file}
            response = self.client.post(url, data=payload, format="multipart")
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @unittest.expectedFailure
    def test_user_create_report_exceed_usage_tokens(self):
        Note.objects.create(
            title="Use up all usage minutes.",
            project=self.project,
            author=self.user,
            # analyzing_tokens=51_000,
        )
        data = {
            "title": "Attempt to add one more report",
            "organizations": [
                {
                    "name": "Test company",
                }
            ],
        }
        self.client.force_authenticate(self.user)
        url = f"/api/projects/{self.project.id}/reports/"
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Assert that the endpoint doesn't create the note.
        self.assertEqual(self.project.notes.count(), 1)

    def test_user_create_report_without_organizations(self):
        data = {
            "title": "Add report without organizations info.",
        }
        self.client.force_authenticate(self.user)
        url = f"/api/projects/{self.project.id}/reports/"
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_outsider_create_report(self):
        data = {
            "title": "Attempt to add report without permission.",
            "organizations": [
                {
                    "name": "Test company",
                }
            ],
        }
        self.client.force_authenticate(self.outsider)
        url = f"/api/projects/{self.project.id}/reports/"
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # Assert that the endpoint doesn't create the note.
        self.assertEqual(self.project.notes.count(), 0)
