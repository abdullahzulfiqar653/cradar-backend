from rest_framework import exceptions, serializers

from api.models.note_template import NoteTemplate
from api.models.note_template_type import NoteTemplateType
from api.models.question import Question
from api.serializers.project import ProjectSerializer
from api.serializers.question import QuestionSerializer


class NoteTemplateSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    project = ProjectSerializer(read_only=True)
    type = serializers.CharField(source="type.name", required=False, allow_null=True)

    class Meta:
        model = NoteTemplate
        fields = [
            "id",
            "title",
            "description",
            "project",
            "type",
        ]


class NoteTemplateDetailSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    description = serializers.CharField(required=False, default="")
    questions = QuestionSerializer(many=True)
    project = ProjectSerializer(read_only=True)
    type = serializers.CharField(source="type.name", required=False, allow_null=True)

    class Meta:
        model = NoteTemplate
        fields = [
            "id",
            "title",
            "description",
            "project",
            "type",
            "questions",
        ]

    def validate_questions(self, value):
        if len(value) < 1:
            raise exceptions.ValidationError("Please provide at least one question.")
        elif len(value) > 8:
            raise exceptions.ValidationError("Please provide at most 8 questions.")
        return value

    def get_note_template_type(self, data, project):
        if data["name"]:
            global_note_template_type = NoteTemplateType.objects.filter(
                name=data["name"], project__isnull=True
            )
            if global_note_template_type.exists():
                note_template_type = global_note_template_type.first()
                return note_template_type
            else:
                note_template_type, _ = NoteTemplateType.objects.get_or_create(
                    name=data["name"], project=project
                )
                return note_template_type

    def create(self, validated_data):
        request = self.context.get("request")

        # Handle NoteTemplateType
        if "type" in validated_data:
            note_template_type_data = validated_data.pop("type")
            note_template_type = self.get_note_template_type(
                note_template_type_data, request.project
            )
            validated_data["type"] = note_template_type

        # Handle Questions
        questions = validated_data.pop("questions", [])
        note_template = NoteTemplate.objects.create(
            **validated_data, project=request.project
        )
        questions_to_create = [
            Question(**question, project=request.project) for question in questions
        ]
        Question.objects.bulk_create(questions_to_create, ignore_conflicts=True)
        questions_to_add = Question.objects.filter(project=request.project).filter(
            title__in=[question["title"] for question in questions]
        )
        note_template.questions.add(*questions_to_add)
        return note_template

    def update(self, note_template: NoteTemplate, validated_data):
        # Handle NoteTemplateType
        if "type" in validated_data:
            note_template_type_data = validated_data.pop("type")
            note_template_type = self.get_note_template_type(
                note_template_type_data, note_template.project
            )
            validated_data["type"] = note_template_type

        # Handle Questions
        questions = validated_data.pop("questions", [])
        note_template.questions.clear()
        questions_to_create = [
            Question(**question, project=note_template.project)
            for question in questions
        ]
        Question.objects.bulk_create(questions_to_create, ignore_conflicts=True)
        questions_to_add = Question.objects.filter(
            project=note_template.project
        ).filter(title__in=[question["title"] for question in questions])
        note_template.questions.add(*questions_to_add)
        return super().update(note_template, validated_data)
