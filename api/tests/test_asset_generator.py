import logging
from textwrap import dedent
from unittest.mock import patch

import numpy as np
from rest_framework.test import APITestCase

from api.ai.generators.asset_generator import generate_content
from api.models.asset import Asset
from api.models.note import Note
from api.models.project import Project
from api.models.takeaway import Takeaway
from api.models.takeaway_type import TakeawayType
from api.models.user import User
from api.models.workspace import Workspace


# Create your tests here.
class TestAssetGenerator(APITestCase):
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

        self.asset = Asset.objects.create(
            title="asset", project=self.project, created_by=self.user
        )
        self.asset.notes.set([self.note])

        return super().setUp()

    @patch("langchain_core.runnables.base.RunnableSequence.invoke")
    def test_create_project_asset_analyze(self, mocked_invoke):
        generate_content(
            self.asset,
            "User's instruction",
            Takeaway.objects.filter(note__assets=self.asset),
            self.user,
        )
        human_prompt = dedent(
            """
                <instruction>User's instruction</instruction>

                <context>
                <content>



                </content>

                <notes>
                - takeaway 1
                - takeaway 2
                </notes>
                </context>
            """
        )
        mocked_invoke.assert_called_once_with({"human_prompt": human_prompt})
