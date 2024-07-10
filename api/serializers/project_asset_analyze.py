from rest_framework import serializers

from api.tasks import analyze_asset


class ProjectAssetAnalyzeSerializer(serializers.Serializer):
    report_ids = serializers.ListField(child=serializers.CharField())

    def validate_report_ids(self, value):
        request = self.context.get("request")
        notes = request.project.notes.filter(id__in=value)
        if not notes:
            raise serializers.ValidationError("No valid reports.")
        if len(notes) > 5:
            raise serializers.ValidationError("Cannot analyze more than 5 reports.")
        if any(note.is_analyzing for note in notes):
            raise serializers.ValidationError("Some reports are being analyzed.")
        return [note.id for note in notes]

    def validate_takeaway_type_ids(self, value):
        request = self.context.get("request")
        takeaway_types = request.project.takeaway_types.filter(id__in=value)
        if not takeaway_types:
            raise serializers.ValidationError("No valid takeaway types.")
        return [takeaway_type.id for takeaway_type in takeaway_types]

    def create(self, validated_data):
        request = self.context.get("request")
        note_ids = validated_data.get("report_ids")
        takeaway_type_ids = list(
            request.project.takeaway_types.values_list("id", flat=True)
        )
        analyze_asset.delay(
            request.project.id, note_ids, takeaway_type_ids, request.user.id
        )
        return validated_data
