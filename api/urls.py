# api/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from api.views.asset.asset import AssetRetrieveUpdateDeleteView
from api.views.asset.asset_block import AssetBlockListView
from api.views.asset.asset_generate import AssetGenerateCreateView
from api.views.block.block import BlockRetrieveView
from api.views.block.block_cluster import BlockClusterCreateView
from api.views.block.block_takeaway import (
    BlockTakeawayDeleteView,
    BlockTakeawayListCreateView,
)
from api.views.block.block_theme import BlockThemeListCreateView
from api.views.demo_generate_takeaways import DemoGenerateTakeawaysCreateView
from api.views.insight.insight import InsightRetrieveUpdateDeleteView
from api.views.insight.insight_tag import InsightTagListView
from api.views.insight.insight_takeaway import (
    InsightTakeawayDeleteView,
    InsightTakeawayListCreateView,
)
from api.views.integrations.googledrive.googledrive_list_files import (
    GoogleDriveListFilesView,
)
from api.views.integrations.googledrive.googledrive_oauth_redirect import (
    GoogleDriveOauthRedirectView,
)
from api.views.integrations.googledrive.googledrive_oauth_url import (
    GoogleDriveOauthUrlRetrieveView,
)
from api.views.note.note import NoteRetrieveUpdateDeleteView
from api.views.note.note_extract import NoteExtractCreateView
from api.views.note.note_keyword import (
    NoteKeywordDestroyView,
    NoteKeywordListCreateView,
)
from api.views.note.note_property import NotePropertyListView, NotePropertyUpdateView
from api.views.note.note_question import (
    NoteQuestionListCreateView,
    NoteQuestionRemainingQuotaRetreiveView,
)
from api.views.note.note_tag import NoteTagListView
from api.views.note.note_tag_generate import NoteTagGenerateView
from api.views.note.note_takeaway import NoteTakeawayListCreateView
from api.views.note.note_takeaway_type import NoteTakeawayTypeListView
from api.views.note_template import NoteTemplateRetrieveUpdateDestroyView
from api.views.note_template_question import NoteTemplateQuestionListView
from api.views.note_type import NoteTypeRetrieveUpdateDestroyView
from api.views.option import OptionRetrieveUpdateDestroyView
from api.views.project.chart.note import ChartNoteCreateView
from api.views.project.chart.takeaway import ChartTakeawayCreateView
from api.views.project.project import ProjectRetrieveUpdateDeleteView
from api.views.project.project_asset import ProjectAssetListCreateView
from api.views.project.project_insight import ProjectInsightListCreateView
from api.views.project.project_invitation import ProjectInvitationCreateView
from api.views.project.project_keyword import ProjectKeywordListView
from api.views.project.project_note import ProjectNoteListCreateView
from api.views.project.project_note_template import ProjectNoteTemplateListCreateView
from api.views.project.project_note_type import ProjectNoteTypeListCreateView
from api.views.project.project_organization import ProjectOrganizationListView
from api.views.project.project_property import ProjectPropertyListCreateView
from api.views.project.project_sentiment import ProjectSentimentListView
from api.views.project.project_summary import ProjectSummaryRetrieveView
from api.views.project.project_tag import ProjectTagListView
from api.views.project.project_takeaway import ProjectTakeawayListView
from api.views.project.project_takeaway_type import ProjectTakeawayTypeListCreateView
from api.views.project.project_user import ProjectUserListView
from api.views.project.project_user_delete import ProjectUserDeleteView
from api.views.property.option import PropertyOptionListCreateView
from api.views.property.property import (
    PropertyDuplicateAPIView,
    PropertyRetrieveUpdateDestroyAPIView,
)
from api.views.saved_items.saved_takeaway import (
    SavedTakeawayDeleteView,
    SavedTakeawayListCreateView,
)
from api.views.takeaway.takeaway import TakeawayRetrieveUpdateDeleteView
from api.views.takeaway.takeaway_tag import (
    TakeawayTagCreateView,
    TakeawayTagDestroyView,
)
from api.views.takeaway_type import TakeawayTypeRetrieveUpdateDestroyView
from api.views.theme.theme import ThemeRetrieveUpdateDestroyView
from api.views.theme.theme_takeaway import (
    ThemeTakeawayDeleteView,
    ThemeTakeawayListCreateView,
)
from api.views.user import UserRetrieveUpdateDestroyView
from api.views.workspace import (
    WorkspaceListCreateView,
    WorkspaceProjectListCreateView,
    WorkspaceUserListUpdateView,
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
        "reports/<str:report_id>/takeaway-types/",
        NoteTakeawayTypeListView.as_view(),
        name="note-takeaway-type-list",
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
    path(
        "reports/<str:report_id>/questions/",
        NoteQuestionListCreateView.as_view(),
        name="note-question-list-create",
    ),
    path(
        "reports/<str:report_id>/questions/remaining-quotas/",
        NoteQuestionRemainingQuotaRetreiveView.as_view(),
        name="note-question-remaining-quota-retrieve",
    ),
    path(
        "reports/<str:report_id>/properties/",
        NotePropertyListView.as_view(),
        name="note-property-list-create",
    ),
    path(
        "reports/<str:report_id>/properties/<str:property_id>/",
        NotePropertyUpdateView.as_view(),
        name="note-property-update",
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
    # Report Types
    # =====================================================
    path(
        "report-types/<str:pk>/",
        NoteTypeRetrieveUpdateDestroyView.as_view(),
        name="note-type-retrieve-update-destroy",
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
        "projects/<str:project_id>/users/delete/",
        ProjectUserDeleteView.as_view(),
        name="project-user-delete",
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
        ProjectNoteTypeListCreateView.as_view(),
        name="project-note-type-list",
    ),
    path(
        "projects/<str:project_id>/takeaway-types/",
        ProjectTakeawayTypeListCreateView.as_view(),
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
    path(
        "projects/<str:project_id>/charts/takeaways/",
        ChartTakeawayCreateView.as_view(),
        name="chart-takeaway-create",
    ),
    path(
        "projects/<str:project_id>/charts/reports/",
        ChartNoteCreateView.as_view(),
        name="chart-report-create",
    ),
    path(
        "projects/<str:project_id>/properties/",
        ProjectPropertyListCreateView.as_view(),
        name="project-property-list-create",
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
        WorkspaceUserListUpdateView.as_view(),
        name="workspace-user-list-update",
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
    # Takeaway Type
    # =====================================================
    path(
        "takeaway-types/<str:pk>/",
        TakeawayTypeRetrieveUpdateDestroyView.as_view(),
        name="takeaway-type-retrieve-update-destroy",
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
        AssetBlockListView.as_view(),
        name="asset-block-list-create",
    ),
    path(
        "assets/<str:asset_id>/generate/",
        AssetGenerateCreateView.as_view(),
        name="asset-generate-create",
    ),
    # =====================================================
    # Block
    # =====================================================
    path(
        "blocks/<str:pk>/",
        BlockRetrieveView.as_view(),
        name="block-retrieve",
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
    path(
        "blocks/<str:block_id>/cluster/",
        BlockClusterCreateView.as_view(),
        name="block-cluster-create",
    ),
    path(
        "blocks/<str:block_id>/themes/",
        BlockThemeListCreateView.as_view(),
        name="block-theme-list-create",
    ),
    # =====================================================
    # Theme
    # =====================================================
    path(
        "themes/<str:pk>/",
        ThemeRetrieveUpdateDestroyView.as_view(),
        name="theme-retrieve-update-destroy",
    ),
    path(
        "themes/<str:theme_id>/takeaways/",
        ThemeTakeawayListCreateView.as_view(),
        name="theme-takeaway-list-create",
    ),
    path(
        "themes/<str:theme_id>/takeaways/delete/",
        ThemeTakeawayDeleteView.as_view(),
        name="theme-takeaway-delete",
    ),
    # =====================================================
    # Property
    # =====================================================
    path(
        "properties/<str:pk>/",
        PropertyRetrieveUpdateDestroyAPIView.as_view(),
        name="property-retrieve-update-destroy",
    ),
    path(
        "properties/<str:property_id>/duplicate/",
        PropertyDuplicateAPIView.as_view(),
        name="property-duplicate",
    ),
    path(
        "properties/<str:property_id>/options/",
        PropertyOptionListCreateView.as_view(),
        name="property-option-list-create",
    ),
    # =====================================================
    # Option
    # =====================================================
    path(
        "options/<str:pk>/",
        OptionRetrieveUpdateDestroyView.as_view(),
        name="option-destroy",
    ),
    # =====================================================
    # Saved
    # =====================================================
    path(
        "saved/takeaways/",
        SavedTakeawayListCreateView.as_view(),
        name="saved-takeaway-list-create",
    ),
    path(
        "saved/takeaways/delete/",
        SavedTakeawayDeleteView.as_view(),
        name="saved-takeaway-list-create",
    ),
    # =====================================================
    # Demo
    # =====================================================
    path(
        "demo/takeaways/",
        DemoGenerateTakeawaysCreateView.as_view(),
        name="demo-generate-takeaway-create",
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
    path(
        "projects/<str:project_id>/integrations/google_drive/oauth-url/",
        GoogleDriveOauthUrlRetrieveView.as_view(),
        name="googledrive-oauth-url",
    ),
    path(
        "projects/<str:project_id>/integrations/google_drive/oauth-redirect/",
        GoogleDriveOauthRedirectView.as_view(),
        name="googledrive-oauth-redirect",
    ),
    path(
        "projects/<str:project_id>/integrations/google_drive/files/",
        GoogleDriveListFilesView.as_view(),
        name="googledrive-files",
    ),
]
