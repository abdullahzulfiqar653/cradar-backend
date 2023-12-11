import logging

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from note.models.organization import Organization
from project.models import Project
from workspace.models import Workspace


class ProjectOrganizationListView(APITestCase):
    def setUp(self):
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

        self.organization1 = Organization.objects.create(
            name="organization", project=self.project
        )
        self.organization2 = Organization.objects.create(
            name="organization with search term", project=self.project
        )
        return super().setUp()

    def test_user_list_organization(self):
        self.client.force_authenticate(self.user)
        url = f"/api/projects/{self.project.id}/organizations/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        self.assertEqual(len(response_json), 2)

    def test_user_list_organization_search(self):
        self.client.force_authenticate(self.user)
        url = f"/api/projects/{self.project.id}/organizations/?search=search%20term"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        self.assertEqual(len(response_json), 1)

    def test_outsider_list_organization(self):
        self.client.force_authenticate(self.outsider)
        url = f"/api/projects/{self.project.id}/organizations/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
