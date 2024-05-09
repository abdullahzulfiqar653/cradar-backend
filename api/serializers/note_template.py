from rest_framework import exceptions, serializers

from api.models.note_template import NoteTemplate
from api.models.question import Question
from api.serializers.question import QuestionSerializer


class NoteTemplateSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)

    class Meta:
        model = NoteTemplate
        fields = [
            "id",
            "title",
            "description",
            "project",
        ]


class NoteTemplateDetailSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    description = serializers.CharField(required=False, default="")
    questions = QuestionSerializer(many=True)

    class Meta:
        model = NoteTemplate
        fields = [
            "id",
            "title",
            "description",
            "questions",
        ]

    def validate_questions(self, value):
        if len(value) < 1:
            raise exceptions.ValidationError("Please provide at least one question.")
        elif len(value) > 8:
            raise exceptions.ValidationError("Please provide at most 8 questions.")
        return value

    def create(self, validated_data):
        request = self.context.get("request")
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
