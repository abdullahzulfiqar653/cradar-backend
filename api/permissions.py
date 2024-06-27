from django.apps import apps
from rest_framework import exceptions, permissions

from api.models.workspace_user import WorkspaceUser


def get_instance(queryset, instance_id):
    try:
        instance = queryset.get(id=instance_id)
    except queryset.model.DoesNotExist:
        raise exceptions.NotFound
    return instance


class InProjectOrWorkspace(permissions.BasePermission):
    """
    To check if the user has permission to access the workspace/project of the resource.

    Note: This permission is only responsible to check for the base resource in the url.
    For example, for endpoint /api/reports/{report_id}/keywords/{keyword_id}
    This permission only checks if the user has access to the report_id.
    The check of keyword_id needs to be done in the view.
    """

    def get_workspace_project(self, request, view):
        match request.path:
            case str(s) if s.startswith("/api/reports/"):
                if not hasattr(request, "note"):
                    Note = apps.get_model("api", "Note")
                    report_id = view.kwargs.get("pk") or view.kwargs.get("report_id")
                    queryset = Note.objects.select_related("project__workspace")
                    request.note = get_instance(queryset, report_id)
                project = request.note.project
                workspace = project.workspace

            case str(s) if s.startswith("/api/report-types/"):
                if not hasattr(request, "note_type"):
                    NoteType = apps.get_model("api", "NoteType")
                    report_type_id = view.kwargs.get("pk") or view.kwargs.get(
                        "report_type_id"
                    )
                    queryset = NoteType.objects.select_related("project__workspace")
                    request.note_type = get_instance(queryset, report_type_id)
                project = request.note_type.project
                workspace = project.workspace

            case str(s) if s.startswith("/api/projects/"):
                if not hasattr(request, "project"):
                    Project = apps.get_model("api", "Project")
                    project_id = view.kwargs.get("pk") or view.kwargs.get("project_id")
                    queryset = Project.objects.select_related("workspace")
                    request.project = get_instance(queryset, project_id)
                project = request.project
                workspace = request.project.workspace

            case str(s) if s.startswith("/api/takeaways/"):
                if not hasattr(request, "takeaway"):
                    Takeaway = apps.get_model("api", "Takeaway")
                    takeaway_id = view.kwargs.get("pk") or view.kwargs.get(
                        "takeaway_id"
                    )
                    queryset = Takeaway.objects.select_related(
                        "note__project__workspace"
                    )
                    request.takeaway = get_instance(queryset, takeaway_id)
                project = request.takeaway.note.project
                workspace = project.workspace

            case str(s) if s.startswith("/api/takeaway-types/"):
                if not hasattr(request, "takeaway_type"):
                    TakeawayType = apps.get_model("api", "TakeawayType")
                    takeaway_type_id = view.kwargs.get("pk") or view.kwargs.get(
                        "takeaway_type_id"
                    )
                    queryset = TakeawayType.objects.select_related("project__workspace")
                    request.takeaway_type = get_instance(queryset, takeaway_type_id)
                project = request.takeaway_type.project
                workspace = project.workspace

            case str(s) if s.startswith("/api/insights/"):
                if not hasattr(request, "insight"):
                    Insight = apps.get_model("api", "Insight")
                    insight_id = view.kwargs.get("pk") or view.kwargs.get("insight_id")
                    queryset = Insight.objects.select_related("project__workspace")
                    request.insight = get_instance(queryset, insight_id)
                project = request.insight.project
                workspace = project.workspace

            case str(s) if s.startswith("/api/assets/"):
                if not hasattr(request, "asset"):
                    Asset = apps.get_model("api", "Asset")
                    asset_id = view.kwargs.get("pk") or view.kwargs.get("asset_id")
                    queryset = Asset.objects.select_related("project__workspace")
                    request.asset = get_instance(queryset, asset_id)
                project = request.asset.project
                workspace = project.workspace

            case str(s) if s.startswith("/api/blocks/"):
                if not hasattr(request, "block"):
                    Block = apps.get_model("api", "Block")
                    block_id = view.kwargs.get("pk") or view.kwargs.get("block_id")
                    queryset = Block.objects.select_related("asset__project__workspace")
                    request.block = get_instance(queryset, block_id)
                project = request.block.asset.project
                workspace = project.workspace

            case str(s) if s.startswith("/api/themes/"):
                if not hasattr(request, "theme"):
                    Theme = apps.get_model("api", "Theme")
                    theme_id = view.kwargs.get("pk") or view.kwargs.get("theme_id")
                    queryset = Theme.objects.select_related(
                        "block__asset__project__workspace"
                    )
                    request.theme = get_instance(queryset, theme_id)
                project = request.theme.block.asset.project
                workspace = project.workspace

            case str(s) if s.startswith("/api/properties/"):
                if not hasattr(request, "property"):
                    Property = apps.get_model("api", "Property")
                    property_id = view.kwargs.get("pk") or view.kwargs.get(
                        "property_id"
                    )
                    queryset = Property.objects.select_related("project__workspace")
                    request.property = get_instance(queryset, property_id)
                project = request.property.project
                workspace = project.workspace

            case str(s) if s.startswith("/api/options/"):
                if not hasattr(request, "option"):
                    Option = apps.get_model("api", "Option")
                    option_id = view.kwargs.get("pk") or view.kwargs.get("option_id")
                    queryset = Option.objects.select_related(
                        "property__project__workspace"
                    )
                    request.option = get_instance(queryset, option_id)
                project = request.option.property.project
                workspace = project.workspace

            case str(s) if s.startswith("/api/workspaces/"):
                if not hasattr(request, "workspace"):
                    Workspace = apps.get_model("api", "Workspace")
                    workspace_id = view.kwargs.get("pk") or view.kwargs.get(
                        "workspace_id"
                    )
                    request.workspace = Workspace.objects.get(id=workspace_id)
                project = None
                workspace = request.workspace

            case _:
                project = None
                workspace = None

        return workspace, project

    def is_authenticated(self, request):
        return bool(request.user and request.user.is_authenticated)

    def is_in_project_or_workspace(self, request, view):
        if not self.is_authenticated(request):
            return False

        workspace, project = self.get_workspace_project(request, view)
        if project:
            if project.users.contains(request.user):
                return project.workspace
            else:
                raise exceptions.NotFound
        elif workspace:
            if workspace.members.contains(request.user):
                return workspace
            else:
                raise exceptions.NotFound
        else:
            return False


class IsWorkspaceOwner(InProjectOrWorkspace):
    def has_permission(self, request, view):
        workspace = self.is_in_project_or_workspace(request, view)
        if not workspace:
            return False

        if hasattr(workspace, "owned_by") and workspace.owned_by == request.user:
            return True
        else:
            return False


class IsWorkspaceEditor(InProjectOrWorkspace):
    def has_permission(self, request, view):
        workspace = self.is_in_project_or_workspace(request, view)
        if not workspace:
            return False

        role = request.user.get_role(workspace)
        if role == WorkspaceUser.Role.EDITOR:
            return True
        else:
            return False


class IsWorkspaceMemberReadOnly(InProjectOrWorkspace):
    def has_permission(self, request, view):
        workspace = self.is_in_project_or_workspace(request, view)
        if not workspace:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            return False


class IsWorkspaceMemberFullAccess(InProjectOrWorkspace):
    def has_permission(self, request, view):
        workspace = self.is_in_project_or_workspace(request, view)
        if not workspace:
            return False
        else:
            return True


IsOwnerEditorOrViewerReadOnly = (
    IsWorkspaceOwner | IsWorkspaceEditor | IsWorkspaceMemberReadOnly
)
