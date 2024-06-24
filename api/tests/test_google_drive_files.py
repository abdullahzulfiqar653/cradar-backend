from unittest.mock import MagicMock, patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.integrations.googledrive.googledrive_user import GoogleDriveUser
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class GoogleDriveFilesViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.force_authenticate(user=self.user)
        self.workspace = Workspace.objects.create(
            name="Test Workspace", owned_by=self.user
        )
        self.project = Project.objects.create(
            id="test_project", name="Test Project", workspace=self.workspace
        )
        self.project.users.add(self.user)
        self.list_files_url = reverse(
            "googledrive-files", kwargs={"project_id": self.project.id}
        )

    @patch("requests.get")
    def test_list_files_success(self, mock_get):
        GoogleDriveUser.objects.create(
            user=self.user,
            access_token="valid_access_token",
            refresh_token="valid_refresh_token",
            token_type="Bearer",
            expires_in=3600,
        )

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "files": [
                {"id": "file1", "name": "File 1", "mimeType": "text/plain"},
                {"id": "file2", "name": "File 2", "mimeType": "image/png"},
            ]
        }

        response = self.client.get(self.list_files_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["name"], "File 1")
        self.assertEqual(response.data[1]["mimeType"], "image/png")

    @patch("requests.get")
    @patch("requests.post")
    def test_list_files_token_expired(self, mock_post, mock_get):
        GoogleDriveUser.objects.create(
            user=self.user,
            access_token="expired_access_token",
            refresh_token="valid_refresh_token",
            token_type="Bearer",
            expires_in=3600,
        )

        # Mock token info response to simulate expired token
        mock_get.side_effect = [
            MagicMock(
                status_code=200, json=MagicMock(return_value={"error": "invalid_token"})
            ),
            MagicMock(
                status_code=200,
                json=MagicMock(return_value={"access_token": "new_access_token"}),
            ),
            MagicMock(status_code=200, json=MagicMock(return_value={"files": []})),
        ]

        # Mock the refresh token API response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"access_token": "new_access_token"}

        response = self.client.get(self.list_files_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    @patch("requests.get")
    def test_list_files_no_google_drive_user(self, mock_get):
        response = self.client.get(self.list_files_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Google Drive account not connected", str(response.data))

    @patch("requests.get")
    @patch("requests.post")
    def test_list_files_failed_to_retrieve_files(self, mock_post, mock_get):
        GoogleDriveUser.objects.create(
            user=self.user,
            access_token="valid_access_token",
            refresh_token="valid_refresh_token",
            token_type="Bearer",
            expires_in=3600,
        )

        # Mock the refresh token API response to succeed
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"access_token": "new_access_token"}

        # Mock the Google Drive API response to fail
        mock_get.side_effect = [
            MagicMock(status_code=200, json=MagicMock(return_value={})),
            MagicMock(status_code=500),
        ]

        response = self.client.get(self.list_files_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Failed to retrieve files from Google Drive", str(response.data))

    @patch("requests.post")
    def test_refresh_access_token_failure(self, mock_post):
        gdrive_user = GoogleDriveUser.objects.create(
            user=self.user,
            access_token="expired_access_token",
            refresh_token="valid_refresh_token",
            token_type="Bearer",
            expires_in=3600,
        )

        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {}

        response = self.client.get(self.list_files_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Failed to refresh access token", str(response.data))
