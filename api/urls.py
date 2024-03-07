# api/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from api.views.asset.asset import AssetRetrieveUpdateDeleteView
from api.views.asset.asset_block import AssetBlockListCreateView
from api.views.block.block import BlockRetrieveUpdateDeleteView
from api.views.block.block_generate import BlockGenerateCreateView
from api.views.block.block_takeaway import (
    BlockTakeawayDeleteView,
    BlockTakeawayListCreateView,
)
from api.views.insight.insight import InsightRetrieveUpdateDeleteView
from api.views.insight.insight_tag import InsightTagListView
from api.views.insight.insight_takeaway import (
    InsightTakeawayDeleteView,
    InsightTakeawayListCreateView,
)
from api.views.note.note import NoteRetrieveUpdateDeleteView
from api.views.note.note_extract import NoteExtractCreateView
from api.views.note.note_keyword import (
    NoteKeywordDestroyView,
    NoteKeywordListCreateView,
)
from api.views.note.note_tag import NoteTagListView
from api.views.note.note_tag_generate import NoteTagGenerateView
from api.views.note.note_takeaway import NoteTakeawayListCreateView
from api.views.note_template import NoteTemplateRetrieveUpdateDestroyView
from api.views.note_template_question import NoteTemplateQuestionListView
from api.views.project.project import ProjectRetrieveUpdateDeleteView
from api.views.project.project_asset import ProjectAssetListCreateView
from api.views.project.project_insight import ProjectInsightListCreateView
from api.views.project.project_invitation import ProjectInvitationCreateView
from api.views.project.project_keyword import ProjectKeywordListView
from api.views.project.project_note import ProjectNoteListCreateView
from api.views.project.project_note_template import ProjectNoteTemplateListCreateView
from api.views.project.project_note_type import ProjectNoteTypeListView
from api.views.project.project_organization import ProjectOrganizationListView
from api.views.project.project_sentiment import ProjectSentimentListView
from api.views.project.project_summary import ProjectSummaryRetrieveView
from api.views.project.project_tag import ProjectTagListView
from api.views.project.project_takeaway import ProjectTakeawayListView
from api.views.project.project_takeaway_type import ProjectTakeawayTypeListView
from api.views.project.project_user import ProjectUserListView
from api.views.takeaway.takeaway import TakeawayRetrieveUpdateDeleteView
from api.views.takeaway.takeaway_tag import (
    TakeawayTagCreateView,
    TakeawayTagDestroyView,
)
from api.views.user import UserRetrieveUpdateDestroyView
from api.views.workspace import (
    WorkspaceListCreateView,
    WorkspaceProjectListCreateView,
    WorkspaceUserListView,
)

from .views.auth import (
    DoPasswordResetView,
    GoogleLoginView,
    InvitationSignupCreateView,
    InvitationStatusRetrieveView,
    PasswordUpdateView,
    RequestPasswordResetView,
    SignupView,
    TokenObtainPairAndRefreshView,
)

urlpatterns = [
    # =====================================================
    # Reports
    # =====================================================
    path(
        "reports/<str:pk>/",
        NoteRetrieveUpdateDeleteView.as_view(),
        name="note-retrieve-update-delete",
    ),
    path(
        "reports/<str:report_id>/takeaways/",
        NoteTakeawayListCreateView.as_view(),
        name="note-takeaway-list-create",
    ),
    path(
        "reports/<str:report_id>/keywords/",
        NoteKeywordListCreateView.as_view(),
        name="note-keyword-list-create",
    ),
    path(
        "reports/<str:report_id>/keywords/<str:keyword_id>/",
        NoteKeywordDestroyView.as_view(),
        name="note-keyword-destroy",
    ),
    path(
        "reports/<str:report_id>/tags/",
        NoteTagListView.as_view(),
        name="note-tag-list",
    ),
    path(
        "reports/<str:report_id>/tags/generate/",
        NoteTagGenerateView.as_view(),
        name="note-tag-generate",
    ),
    path(
        "reports/<str:report_id>/extract/",
        NoteExtractCreateView.as_view(),
        name="note-extract",
    ),
    # =====================================================
    # Report Templates
    # =====================================================
    path(
        "report-templates/<str:pk>/",
        NoteTemplateRetrieveUpdateDestroyView.as_view(),
        name="note-template-retrieve-update-delete",
    ),
    path(
        "report-templates/<str:report_template_id>/questions/",
        NoteTemplateQuestionListView.as_view(),
        name="note-template-question-list",
    ),
    # =====================================================
    # Projects
    # =====================================================
    path(
        "projects/<str:pk>/",
        ProjectRetrieveUpdateDeleteView.as_view(),
        name="project-retrieve-update-delete",
    ),
    path(
        "projects/<str:project_id>/users/",
        ProjectUserListView.as_view(),
        name="project-user-list",
    ),
    path(
        "projects/<str:project_id>/reports/",
        ProjectNoteListCreateView.as_view(),
        name="project-note-list-create",
    ),
    path(
        "projects/<str:project_id>/takeaways/",
        ProjectTakeawayListView.as_view(),
        name="project-takeaway-list",
    ),
    path(
        "projects/<str:project_id>/tags/",
        ProjectTagListView.as_view(),
        name="project-tag-list",
    ),
    path(
        "projects/<str:project_id>/organizations/",
        ProjectOrganizationListView.as_view(),
        name="project-organization-list",
    ),
    path(
        "projects/<str:project_id>/keywords/",
        ProjectKeywordListView.as_view(),
        name="project-keyword-list",
    ),
    path(
        "projects/<str:project_id>/sentiments/",
        ProjectSentimentListView.as_view(),
        name="project-sentiment-list",
    ),
    path(
        "projects/<str:project_id>/report-types/",
        ProjectNoteTypeListView.as_view(),
        name="project-note-type-list",
    ),
    path(
        "projects/<str:project_id>/takeaway-types/",
        ProjectTakeawayTypeListView.as_view(),
        name="project-takeaway-type-list",
    ),
    path(
        "projects/<str:project_id>/insights/",
        ProjectInsightListCreateView.as_view(),
        name="project-insight-list-create",
    ),
    path(
        "projects/<str:project_id>/invitations/",
        ProjectInvitationCreateView.as_view(),
        name="project-invite",
    ),
    path(
        "projects/<str:project_id>/summary/",
        ProjectSummaryRetrieveView.as_view(),
        name="project-summary-retrieve",
    ),
    path(
        "projects/<str:project_id>/report-templates/",
        ProjectNoteTemplateListCreateView.as_view(),
        name="project-note-template-list-create",
    ),
    path(
        "projects/<str:project_id>/assets/",
        ProjectAssetListCreateView.as_view(),
        name="project-asset-list-create",
    ),
    # =====================================================
    # Workspace
    # =====================================================
    path(
        "workspaces/",
        WorkspaceListCreateView.as_view(),
        name="workspace-list-create",
    ),
    path(
        "workspaces/<str:workspace_id>/projects/",
        WorkspaceProjectListCreateView.as_view(),
        name="workspace-project-list-create",
    ),
    path(
        "workspaces/<str:pk>/users/",
        WorkspaceUserListView.as_view(),
        name="workspace-user-list",
    ),
    # =====================================================
    # Takeaway
    # =====================================================
    path(
        "takeaways/<str:pk>/",
        TakeawayRetrieveUpdateDeleteView.as_view(),
        name="takeaway-retrieve-update-delete",
    ),
    path(
        "takeaways/<str:takeaway_id>/tags/",
        TakeawayTagCreateView.as_view(),
        name="takeaway-tag-create",
    ),
    path(
        "takeaways/<str:takeaway_id>/tags/<str:tag_id>/",
        TakeawayTagDestroyView.as_view(),
        name="takeaway-tag-destroy",
    ),
    # =====================================================
    # Insight
    # =====================================================
    path(
        "insights/<str:pk>/",
        InsightRetrieveUpdateDeleteView.as_view(),
        name="insight-retrieve-update-delete",
    ),
    path(
        "insights/<str:insight_id>/takeaways/",
        InsightTakeawayListCreateView.as_view(),
        name="insight-takeaway-list-create",
    ),
    path(
        "insights/<str:insight_id>/takeaways/delete/",
        InsightTakeawayDeleteView.as_view(),
        name="insight-takeaway-delete",
    ),
    path(
        "insights/<str:insight_id>/tags/",
        InsightTagListView.as_view(),
        name="insight-tag-list",
    ),
    # =====================================================
    # Asset
    # =====================================================
    path(
        "assets/<str:pk>/",
        AssetRetrieveUpdateDeleteView.as_view(),
        name="asset-retrieve-update-delete",
    ),
    path(
        "assets/<str:asset_id>/blocks/",
        AssetBlockListCreateView.as_view(),
        name="asset-block-list-create",
    ),
    # =====================================================
    # Block
    # =====================================================
    path(
        "blocks/<str:pk>/",
        BlockRetrieveUpdateDeleteView.as_view(),
        name="block-retrieve-update-delete",
    ),
    path(
        "blocks/<str:block_id>/generate/",
        BlockGenerateCreateView.as_view(),
        name="block-generate-create",
    ),
    path(
        "blocks/<str:block_id>/takeaways/",
        BlockTakeawayListCreateView.as_view(),
        name="block-takeaway-list-create",
    ),
    path(
        "blocks/<str:block_id>/takeaways/delete/",
        BlockTakeawayDeleteView.as_view(),
        name="block-takeaway-delete",
    ),
    # =====================================================
    # Auth
    # =====================================================
    path(
        "token/",
        TokenObtainPairAndRefreshView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "token/google/",
        GoogleLoginView.as_view(),
        name="google-token-obtain-pair",
    ),
    path(
        "signup/",
        SignupView.as_view(),
        name="signup-create",
    ),
    path(
        "invitation/signup/",
        InvitationSignupCreateView.as_view(),
        name="invited-signup-create",
    ),
    path(
        "invitation/<str:token>/",
        InvitationStatusRetrieveView.as_view(),
        name="invitation-status-retrieve",
    ),
    path(
        "auth-users/",
        UserRetrieveUpdateDestroyView.as_view(),
        name="auth-user-retrieve-update",
    ),
    path(
        "password/update/",
        PasswordUpdateView.as_view(),
        name="password-update",
    ),
    path(
        "password/request-reset/",
        RequestPasswordResetView.as_view(),
        name="password-request-reset",
    ),
    path(
        "password/do-reset/",
        DoPasswordResetView.as_view(),
        name="password-do-reset",
    ),
]
