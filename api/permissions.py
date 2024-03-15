from django.apps import apps
from rest_framework import exceptions, permissions


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
                Note = apps.get_model("api", "Note")
                report_id = view.kwargs.get("pk") or view.kwargs.get("report_id")
                queryset = Note.objects.select_related("project__workspace")
                request.note = get_instance(queryset, report_id)
                project = request.note.project
                workspace = project.workspace

            case str(s) if s.startswith("/api/report-templates/"):
                NoteTemplate = apps.get_model("api", "NoteTemplate")
                report_template_id = view.kwargs.get("pk") or view.kwargs.get(
                    "report_template_id"
                )
                queryset = NoteTemplate.objects.select_related("project__workspace")
                request.note_template = get_instance(queryset, report_template_id)
                project = request.note_template.project
                if project is None:
                    # For public report templates, project is None
                    if request.method in permissions.SAFE_METHODS:
                        workspace = None
                    else:
                        # We don't allow creating / updating public report templates
                        raise exceptions.PermissionDenied
                else:
                    workspace = project.workspace

            case str(s) if s.startswith("/api/projects/"):
                Project = apps.get_model("api", "Project")
                project_id = view.kwargs.get("pk") or view.kwargs.get("project_id")
                queryset = Project.objects.select_related("workspace")
                request.project = get_instance(queryset, project_id)
                project = request.project
                workspace = request.project.workspace

            case str(s) if s.startswith("/api/takeaways/"):
                Takeaway = apps.get_model("api", "Takeaway")
                takeaway_id = view.kwargs.get("pk") or view.kwargs.get("takeaway_id")
                queryset = Takeaway.objects.select_related("note__project__workspace")
                request.takeaway = get_instance(queryset, takeaway_id)
                project = request.takeaway.note.project
                workspace = project.workspace

            case str(s) if s.startswith("/api/insights/"):
                Insight = apps.get_model("api", "Insight")
                insight_id = view.kwargs.get("pk") or view.kwargs.get("insight_id")
                queryset = Insight.objects.select_related("project__workspace")
                request.insight = get_instance(queryset, insight_id)
                project = request.insight.project
                workspace = project.workspace

            case str(s) if s.startswith("/api/assets/"):
                Asset = apps.get_model("api", "Asset")
                asset_id = view.kwargs.get("pk") or view.kwargs.get("asset_id")
                queryset = Asset.objects.select_related("project__workspace")
                request.asset = get_instance(queryset, asset_id)
                project = request.asset.project
                workspace = project.workspace

            case str(s) if s.startswith("/api/blocks/"):
                Block = apps.get_model("api", "Block")
                block_id = view.kwargs.get("pk") or view.kwargs.get("block_id")
                queryset = Block.objects.select_related("asset__project__workspace")
                request.block = get_instance(queryset, block_id)
                project = request.block.asset.project
                workspace = project.workspace

            case "/api/workspaces/":
                project = None
                workspace = None

            case str(s) if s.startswith("/api/workspaces/"):
                Workspace = apps.get_model("api", "Workspace")
                workspace_id = view.kwargs.get("pk") or view.kwargs.get("workspace_id")
                request.workspace = Workspace.objects.get(id=workspace_id)
                project = None
                workspace = request.workspace

            case _:
                project = None
                workspace = None

        return workspace, project

    def is_authenticated(self, request):
        return bool(request.user and request.user.is_authenticated)

    def has_permission(self, request, view):
        if not self.is_authenticated(request):
            return False

        workspace, project = self.get_workspace_project(request, view)

        if project:
            if project.users.contains(request.user):
                return True
            else:
                raise exceptions.NotFound
        elif workspace:
            if workspace.members.contains(request.user):
                return True
            else:
                raise exceptions.NotFound
        else:
            return True


class IsWorkspaceOwner(InProjectOrWorkspace):
    def has_permission(self, request, view):
        workspace, project = self.get_workspace_project(request, view)
        if hasattr(workspace, "owned_by") and workspace.owned_by == request.user:
            return True
        else:
            return False
