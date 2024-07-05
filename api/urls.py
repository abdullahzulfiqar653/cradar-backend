# api/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from api.views.asset.asset import AssetRetrieveUpdateDeleteView
from api.views.asset.asset_block import AssetBlockListView
from api.views.asset.asset_generate import AssetGenerateCreateView
from api.views.asset.asset_takeaway import AssetTakeawayListView
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
from api.views.integrations.mixpanel.event import MixpanelEventCreateView
from api.views.integrations.slack.channel import SlackChannelsListView
from api.views.integrations.slack.event import SlackEventsCreateView
from api.views.integrations.slack.oauth_redirect import SlackOauthRedirectCreateView
from api.views.integrations.slack.oauth_url import SlackOauthUrlRetrieveView
from api.views.integrations.slack.to_frontend import SlackToFrontendRedirectView
from api.views.note.note import NoteRetrieveUpdateDeleteView
from api.views.note.note_keyword import (
    NoteKeywordDestroyView,
    NoteKeywordListCreateView,
)
from api.views.note.note_message import NoteMessageListCreateView
from api.views.note.note_property import NotePropertyListView, NotePropertyUpdateView
from api.views.note.note_tag import NoteTagListView
from api.views.note.note_takeaway import NoteTakeawayListCreateView
from api.views.note.note_takeaway_type import NoteTakeawayTypeListCreateView
from api.views.note_type import NoteTypeRetrieveUpdateDestroyView
from api.views.option import OptionRetrieveUpdateDestroyView
from api.views.project.chart.note import ChartNoteCreateView
from api.views.project.chart.takeaway import ChartTakeawayCreateView
from api.views.project.project import ProjectRetrieveUpdateDeleteView
from api.views.project.project_asset import ProjectAssetListCreateView
from api.views.project.project_asset_analyze import ProjectAssetAnalyzeCreateView
from api.views.project.project_insight import ProjectInsightListCreateView
from api.views.project.project_invitation import ProjectInvitationCreateView
from api.views.project.project_keyword import ProjectKeywordListView
from api.views.project.project_note import ProjectNoteListCreateView
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
from api.views.stripe.webhook import StripeWebhookView
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
from api.views.workspace.customer_billing_portal_session import (
    StripeBillingPortalSessionCreateView,
)
from api.views.workspace.workspace import (
    WorkspaceListCreateView,
    WorkspaceRetrieveUpdateView,
    WorkspaceUserListUpdateView,
)
from api.views.workspace.workspace_project import WorkspaceProjectListCreateView

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
        NoteTakeawayTypeListCreateView.as_view(),
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
        "reports/<str:report_id>/properties/",
        NotePropertyListView.as_view(),
        name="note-property-list-create",
    ),
    path(
        "reports/<str:report_id>/properties/<str:property_id>/",
        NotePropertyUpdateView.as_view(),
        name="note-property-update",
    ),
    path(
        "reports/<str:report_id>/messages/",
        NoteMessageListCreateView.as_view(),
        name="note-message-list-create",
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
        "projects/<str:project_id>/assets/",
        ProjectAssetListCreateView.as_view(),
        name="project-asset-list-create",
    ),
    path(
        "projects/<str:project_id>/assets/analyze/",
        ProjectAssetAnalyzeCreateView.as_view(),
        name="project-asset-analyze",
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
        "workspaces/<str:workspace_id>/billing-portal-session/",
        StripeBillingPortalSessionCreateView.as_view(),
        name="workspace-billing-portal-session",
    ),
    path(
        "workspaces/",
        WorkspaceListCreateView.as_view(),
        name="workspace-list-create",
    ),
    path(
        "workspaces/<str:pk>/",
        WorkspaceRetrieveUpdateView.as_view(),
        name="workspace-retrieve-update",
    ),
    path(
        "workspaces/<str:workspace_id>/projects/",
        WorkspaceProjectListCreateView.as_view(),
        name="workspace-project-list-create",
    ),
    path(
        "workspaces/<str:workspace_id>/users/",
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
        "assets/<str:asset_id>/takeaways/",
        AssetTakeawayListView.as_view(),
        name="asset-takeaway-list-create",
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
    # =====================================================
    # Mixpanel
    # =====================================================
    path(
        "integrations/mixpanel/event/",
        MixpanelEventCreateView.as_view(),
        name="mixpanel-event-create",
    ),
    # =====================================================
    # Stripe
    # =====================================================
    path(
        "stripe/webhook/",
        StripeWebhookView.as_view(),
        name="stripe-webhook",
    ),
    # =====================================================
    # Slack Integration
    # =====================================================
    path(
        "integrations/slack/oauth-url/",
        SlackOauthUrlRetrieveView.as_view(),
        name="oauth_url",
    ),
    path(
        "integrations/slack/oauth-redirect/",
        SlackOauthRedirectCreateView.as_view(),
        name="slack_oauth_redirect",
    ),
    path(
        "integrations/slack/events/",
        SlackEventsCreateView.as_view(),
        name="slack_events",
    ),
    path(
        "integrations/slack/to-frontend/",
        SlackToFrontendRedirectView.as_view(),
        name="slack_to_frontend",
    ),
    path(
        "integrations/slack/channels/",
        SlackChannelsListView.as_view(),
        name="list_channels",
    ),
]
