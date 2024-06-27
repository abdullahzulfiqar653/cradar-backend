import logging
from unittest.mock import patch

import numpy as np
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.note import Note
from api.models.project import Project
from api.models.takeaway import Takeaway
from api.models.takeaway_type import TakeawayType
from api.models.user import User
from api.models.workspace import Workspace


# Create your tests here.
class TestProjectAssetAnalyzeCreateView(APITestCase):
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
            title="note", project=self.project, author=self.user
        )
        self.takeaway_type1 = TakeawayType.objects.create(
            name="takeaway type 1", project=self.project
        )
        self.takeaway1 = Takeaway.objects.create(
            title="takeaway 1",
            note=self.note,
            created_by=self.user,
            type=self.takeaway_type1,
            vector=np.random.rand(1536),
        )
        self.takeaway_type2 = TakeawayType.objects.create(
            name="takeaway type 2", project=self.project
        )
        self.takeaway2 = Takeaway.objects.create(
            title="takeaway 2",
            note=self.note,
            created_by=self.user,
            type=self.takeaway_type2,
            vector=np.random.rand(1536),
        )

        return super().setUp()

    @patch("api.tasks.analyze_asset.delay")
    def test_create_project_asset_analyze(self, mocked_delay):
        url = f"/api/projects/{self.project.id}/assets/analyze/"
        data = {
            "report_ids": [self.note.id],
            "takeaway_type_ids": [self.takeaway_type1.id, self.takeaway_type2.id],
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mocked_delay.assert_called_once_with(
            self.project.id,
            [self.note.id],
            [self.takeaway_type1.id, self.takeaway_type2.id],
            self.user.id,
        )

    def test_create_project_asset_analyze_with_invalid_report_id(self):
        outsider_workspace = Workspace.objects.create(
            name="outsider workspace", owned_by=self.outsider
        )
        outsider_project = Project.objects.create(
            name="outsider project", workspace=outsider_workspace
        )
        outsider_note = Note.objects.create(
            title="outsider note", project=outsider_project, author=self.outsider
        )

        url = f"/api/projects/{self.project.id}/assets/analyze/"
        data = {
            "report_ids": [outsider_note.id],
            "takeaway_type_ids": [self.takeaway_type1.id, self.takeaway_type2.id],
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
