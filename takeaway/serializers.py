from rest_framework import exceptions, serializers

from note.models import Note
from tag.serializers import TagSerializer
from takeaway.models import Highlight, Insight, Takeaway
from user.serializers import AuthUserSerializer


class BriefNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = [
            "id",
            "title",
        ]


class TakeawaySerializer(serializers.ModelSerializer):
    created_by = AuthUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    report = BriefNoteSerializer(source="note", read_only=True)

    class Meta:
        model = Takeaway
        fields = [
            "id",
            "title",
            "tags",
            "description",
            "status",
            "created_by",
            "report",
            "created_at",
        ]

    def create(self, validated_data):
        report_id = self.context["view"].kwargs["report_id"]
        request = self.context["request"]
        note = Note.objects.filter(id=report_id).first()
        if note is None or not note.project.users.contains(request.user):
            exceptions.NotFound("Report is not found.")

        validated_data["created_by"] = request.user
        validated_data["note"] = note
        return super().create(validated_data)


class HighlightSerializer(TakeawaySerializer):
    class Meta:
        model = Highlight
        fields = [
            "id",
            "start",
            "end",
        ]

    def validate(self, data):
        start = data["start"]
        end = data["end"]
        if not (0 <= start < end):
            raise serializers.ValidationError(
                "start and end must satisfy the condition: " "0 <= start < end."
            )
        return super().validate(data)

    def create(self, validated_data):
        report_id = self.context["view"].kwargs["report_id"]
        note = Note.objects.filter(id=report_id).first()
        request = self.context["request"]
        if note is None or not note.project.users.contains(request.user):
            exceptions.NotFound("Report is not found.")

        request = self.context["request"]
        validated_data["created_by"] = request.user
        validated_data["note"] = note
        return super().create(validated_data)

    def to_representation(self, instance):
        # Overwriting TakeawaySerializer.to_representation with rest_framework original function
        return super(TakeawaySerializer, self).to_representation(instance)


class ProjectInsightSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    created_by = AuthUserSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    takeaway_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Insight
        fields = [
            "id",
            "title",
            "created_at",
            "created_by",
            "takeaway_count",
        ]

    def create(self, validated_data):
        project_id = self.context["view"].kwargs["project_id"]
        request = self.context["request"]
        project = request.user.projects.filter(id=project_id).first()
        if project is None:
            exceptions.NotFound("Project not found.")
        validated_data["project"] = project
        validated_data["created_by"] = request.user
        return super().create(validated_data)


class InsightSerializer(serializers.ModelSerializer):
    takeaways = TakeawaySerializer(many=True, read_only=True)
    created_by = AuthUserSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Insight
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "created_by",
            "takeaways",
        ]


class InsightTakeawaySerializer(serializers.Serializer):
    id = serializers.CharField()

    def validate_id(self, value):
        if value not in self.context["valid_takeaway_ids"]:
            raise exceptions.ValidationError(
                f"Takeaway {value} not in the insight project."
            )
        return value


class InsightTakeawaysSerializer(serializers.Serializer):
    takeaways = InsightTakeawaySerializer(many=True)

    def create(self, validated_data):
        insight: Insight = self.context["insight"]
        takeaway_ids = {takeaway["id"] for takeaway in validated_data["takeaways"]}
        # Skip adding takeaways that are already in insight
        takeaways_to_add = Takeaway.objects.filter(id__in=takeaway_ids).exclude(
            insights=insight
        )
        for takeaway in takeaways_to_add:
            insight.takeaways.add(takeaway)
        return {"takeaways": takeaways_to_add}

    def delete(self):
        insight: Insight = self.context["insight"]
        takeaway_ids = {takeaway["id"] for takeaway in self.validated_data["takeaways"]}
        # Only remove takeaways that are in insight
        takeaways_to_remove = insight.takeaways.filter(id__in=takeaway_ids)
        for takeaway in takeaways_to_remove:
            insight.takeaways.remove(takeaway)
        self.instance = {"takeaways": takeaways_to_remove}
