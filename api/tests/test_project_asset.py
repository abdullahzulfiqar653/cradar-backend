import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.asset import Asset
from api.models.note import Note
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class TestProjectAssetListCreateView(APITestCase):
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

        self.note = Note.objects.create(
            title="note 1", project=self.project, author=self.user
        )
        return super().setUp()

    def test_user_create_asset(self):
        data = {
            "title": "test asset",
            "report_ids": [self.note.id],
        }
        url = f"/api/projects/{self.project.id}/assets/"
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_json = response.json()
        asset = Asset.objects.get(id=response_json["id"])
        self.assertEqual(asset.title, data["title"])

    def test_user_create_asset_without_title(self):
        data = {
            "report_ids": [self.note.id],
        }
        url = f"/api/projects/{self.project.id}/assets/"
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_json = response.json()
        asset = Asset.objects.get(id=response_json["id"])
        self.assertEqual(asset.title, "")

    def test_user_create_asset_without_report_ids(self):
        data = {
            "title": "test asset",
        }
        url = f"/api/projects/{self.project.id}/assets/"
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_outsider_create_asset(self):
        data = {
            "title": "test asset",
        }
        url = f"/api/projects/{self.project.id}/assets/"
        self.client.force_authenticate(self.outsider)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_list_asset(self):
        asset1 = Asset.objects.create(
            title="test asset 1",
            project=self.project,
            created_by=self.user,
        )
        asset2 = Asset.objects.create(
            title="test asset 2",
            project=self.project,
            created_by=self.user,
        )
        asset3 = Asset.objects.create(
            title="test asset 3",
            project=self.project,
            created_by=self.user,
        )
        url = f"/api/projects/{self.project.id}/assets/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_asset_ids = [asset["id"] for asset in response.json()]
        self.assertCountEqual(response_asset_ids, [asset1.id, asset2.id, asset3.id])
