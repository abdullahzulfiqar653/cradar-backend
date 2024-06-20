from django_filters import rest_framework as filters

from api.filters.patch import ModelMultipleChoiceFilter
from api.models.keyword import Keyword
from api.models.note import Note, Organization
from api.models.note_type import NoteType
from api.models.project import Project


def notes_in_project(request):
    project_id = request.parser_context["kwargs"]["project_id"]
    return Note.objects.filter(project_id=project_id)


def users_in_project(request):
    project_id = request.parser_context["kwargs"]["project_id"]
    return Project.objects.get(id=project_id).users.all()


def organizations_in_project(request):
    project_id = request.parser_context["kwargs"]["project_id"]
    return Organization.objects.filter(project_id=project_id)


def keywords_in_project(request):
    project_id = request.parser_context["kwargs"]["project_id"]
    return Keyword.objects.filter(notes__project=project_id)


def note_types_in_project(request):
    project_id = request.parser_context["kwargs"]["project_id"]
    return NoteType.objects.filter(project_id=project_id)


class NoteFilter(filters.FilterSet):
    organization = ModelMultipleChoiceFilter(
        field_name="organizations__name",
        to_field_name="name",
        queryset=organizations_in_project,
    )
    type = ModelMultipleChoiceFilter(
        field_name="type__name", to_field_name="name", queryset=note_types_in_project
    )
    revenue = filters.MultipleChoiceFilter(choices=Note.Revenue.choices)
    sentiment = filters.MultipleChoiceFilter(choices=Note.Sentiment.choices)
    author = ModelMultipleChoiceFilter(
        field_name="author__username",
        to_field_name="username",
        queryset=users_in_project,
    )
    keyword = ModelMultipleChoiceFilter(
        field_name="keywords__name",
        to_field_name="name",
        queryset=keywords_in_project,
    )
    created_at = filters.DateFromToRangeFilter(field_name="created_at")
