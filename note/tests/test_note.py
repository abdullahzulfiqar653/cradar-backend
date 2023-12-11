import logging

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from note.models import Note
from note.models.organization import Organization
from project.models import Project
from tag.models import Keyword
from takeaway.models import Highlight
from workspace.models import Workspace


# Create your tests here.
class TestNoteKeywordDestroyView(APITestCase):
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

        self.note = Note.objects.create(
            title="note", project=self.project, author=self.user
        )
        self.existing_keyword = Keyword.objects.create(name="keyword")
        self.note.keywords.add(self.existing_keyword)
        return super().setUp()

    def test_user_delete_insight_takeaways(self):
        self.client.force_authenticate(self.user)
        keyword_id = self.existing_keyword.id
        url = f"/api/reports/{self.note.id}/keywords/{keyword_id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(self.note.keywords.contains(self.existing_keyword))

    def test_user_delete_nonexisting_insight_takeaways(self):
        self.client.force_authenticate(self.user)
        non_existing_keyword_id = "nonexistenceid"
        url = f"/api/reports/{self.note.id}/keywords/{non_existing_keyword_id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_delete_insight_takeaways(self):
        self.client.force_authenticate(self.outsider)
        keyword_id = self.existing_keyword.id
        url = f"/api/reports/{self.note.id}/keywords/{keyword_id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(self.note.keywords.contains(self.existing_keyword))


class TestNoteRetrieveUpdateDeleteView(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="user", password="password")

        workspace = Workspace.objects.create(name="workspace")
        self.project = Project.objects.create(name="project", workspace=workspace)
        self.project.users.add(self.user)

        self.note = Note.objects.create(
            title="note",
            project=self.project,
            author=self.user,
            content="This is a sample text only.",
        )
        return super().setUp()

    def test_highlight_remain_after_user_edit_note_content(self):
        highlight = Highlight.objects.create(
            start=10,
            end=16,
            note=self.note,
            created_by=self.user,
        )
        self.client.force_authenticate(self.user)
        url = f"/api/reports/{self.note.id}/"
        data = {
            "content": "This is an edited sample text.",
            "highlights": [
                {
                    "id": highlight.id,
                    "start": 18,
                    "end": 24,
                }
            ],
        }
        response = self.client.patch(url, data=data)
        highlight.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.note.highlights.contains(highlight))
        self.assertEqual(highlight.title, "sample")
        self.assertEqual(highlight.start, 18)
        self.assertEqual(highlight.end, 24)

    def test_user_update_note_organization(self):
        self.client.force_authenticate(self.user)
        url = f"/api/reports/{self.note.id}/"

        # Test add organization
        data = {"organizations": [{"name": "added organization"}]}
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.note.organizations.count(), 1)
        organization1 = self.note.organizations.first()
        self.assertEqual(organization1.name, "added organization")

        # Test replace organization
        data = {"organizations": [{"name": "replaced organization"}]}
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.note.organizations.count(), 1)
        organization2 = self.note.organizations.first()
        self.assertEqual(organization2.name, "replaced organization")
        self.assertEqual(
            Organization.objects.filter(id=organization1.id).count(),
            0,
            "Organization that is not related to any note is not cleaned up.",
        )
