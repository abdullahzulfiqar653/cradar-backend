import datetime
import logging

from dateutil import parser
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.asset import Asset
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


# Create your tests here.
class TestAssetRetrieveUpdateDeleteView(APITestCase):
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
        self.asset = Asset.objects.create(
            title="asset", project=self.project, created_by=self.user
        )
        self.project.users.add(self.user)
        return super().setUp()

    def test_user_retrieve_asset_details(self):
        self.client.force_authenticate(self.user)
        url = f"/api/assets/{self.asset.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["title"], "asset")

    def test_user_cannot_update_asset_created_at(self):
        self.client.force_authenticate(self.user)
        url = f"/api/assets/{self.asset.id}/"
        now_utc = datetime.datetime.now().astimezone(datetime.timezone.utc)
        data = {"created_at": now_utc}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_created_at = parser.parse(response.json()["created_at"]).astimezone(
            datetime.timezone.utc
        )
        self.assertEqual(response_created_at, self.asset.created_at)

    def test_user_delete_asset(self):
        self.client.force_authenticate(self.user)
        url = f"/api/assets/{self.asset.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_retrieve_asset_details(self):
        self.client.force_authenticate(self.outsider)
        url = f"/api/assets/{self.asset.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_delete_insight(self):
        self.client.force_authenticate(self.outsider)
        url = f"/api/assets/{self.asset.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
