from django_filters import rest_framework as filters

from api.models.note import Note
from api.models.project import Project
from api.models.tag import Tag
from api.models.takeaway import Takeaway
from api.models.takeaway_type import TakeawayType
from api.models.user import User


def users_in_scope(request):
    "Return the list of users in project or insight"
    kwargs = request.parser_context["kwargs"]

    project_id = kwargs.get("project_id")
    if project_id is not None:
        return Project.objects.get(id=project_id).users.all()

    report_id = kwargs.get("report_id")
    if report_id is not None:
        return User.objects.filter(projects__notes=report_id)

    insight_id = kwargs.get("insight_id")
    if insight_id is not None:
        return User.objects.filter(created_takeaways__insights=insight_id)

    asset_id = kwargs.get("asset_id")
    if asset_id is not None:
        return User.objects.filter(projects__assets=asset_id)

    block_id = kwargs.get("block_id")
    if block_id is not None:
        return User.objects.filter(projects__assets__blocks=block_id)

    return User.objects.none()


def tags_in_scope(request):
    "Return the list of tags in project or insight"
    kwargs = request.parser_context["kwargs"]

    project_id = kwargs.get("project_id")
    if project_id is not None:
        return Tag.objects.filter(takeaways__note__project=project_id)

    report_id = kwargs.get("report_id")
    if report_id is not None:
        return Tag.objects.filter(takeaways__note=report_id)

    insight_id = kwargs.get("insight_id")
    if insight_id is not None:
        return Tag.objects.filter(takeaways__insights=insight_id)

    asset_id = kwargs.get("asset_id")
    if asset_id is not None:
        return Tag.objects.filter(takeaways__note__project__assets=asset_id)

    block_id = kwargs.get("block_id")
    if block_id is not None:
        return Tag.objects.filter(takeaways__note__project__assets__blocks=block_id)

    return Tag.objects.none()


def notes_in_scope(request):
    "Return the list of notes in project"
    kwargs = request.parser_context["kwargs"]

    project_id = kwargs.get("project_id")
    if project_id is not None:
        return Note.objects.filter(project_id=project_id)

    insight_id = kwargs.get("insight_id")
    if insight_id is not None:
        return Note.objects.filter(takeaways__insights=insight_id)

    asset_id = kwargs.get("asset_id")
    if asset_id is not None:
        return Note.objects.filter(project__assets=asset_id)

    block_id = kwargs.get("block_id")
    if block_id is not None:
        return Note.objects.filter(project__assets__blocks=block_id)

    return Note.objects.none()


def takeaway_types_in_scope(request):
    "Return the list of takeaway types in project"
    kwargs = request.parser_context["kwargs"]

    project_id = kwargs.get("project_id")
    if project_id is not None:
        return TakeawayType.objects.filter(takeaways__note__project_id=project_id)

    report_id = kwargs.get("report_id")
    if report_id is not None:
        return TakeawayType.objects.filter(takeaways__note=report_id)

    insight_id = kwargs.get("insight_id")
    if insight_id is not None:
        return TakeawayType.objects.filter(takeaways__insights=insight_id)

    asset_id = kwargs.get("asset_id")
    if asset_id is not None:
        return TakeawayType.objects.filter(takeaways__note__project__assets=asset_id)

    block_id = kwargs.get("block_id")
    if block_id is not None:
        return TakeawayType.objects.filter(
            takeaways__note__project__assets__blocks=block_id
        )

    return TakeawayType.objects.none()


class TakeawayFilter(filters.FilterSet):
    created_by = filters.ModelMultipleChoiceFilter(
        field_name="created_by__username",
        to_field_name="username",
        queryset=users_in_scope,
    )
    tag = filters.ModelMultipleChoiceFilter(
        field_name="tags__name", to_field_name="name", queryset=tags_in_scope
    )
    report_id = filters.ModelMultipleChoiceFilter(
        field_name="note", to_field_name="id", queryset=notes_in_scope
    )
    priority = filters.MultipleChoiceFilter(choices=Takeaway.Priority.choices)
    type = filters.ModelMultipleChoiceFilter(
        field_name="type__name", to_field_name="name", queryset=takeaway_types_in_scope
    )
    report_type = filters.ModelMultipleChoiceFilter(
        field_name="note__type", to_field_name="type", queryset=notes_in_scope
    )

    class Meta:
        model = Takeaway
        fields = ["priority", "tag", "created_by", "type", "report_type", "report_id"]


class NoteTakeawayFilter(TakeawayFilter):
    report_id = None
    report_type = None

    class Meta:
        model = Takeaway
        fields = ["priority", "tag", "created_by", "type"]
