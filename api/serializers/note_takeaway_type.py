from rest_framework import serializers

from api.models.user import User
from api.tasks import analyze_existing_note


class NoteTakeawayTypeSerializer(serializers.Serializer):
    takeaway_type_ids = serializers.ListField(child=serializers.CharField())

    def validate_takeaway_type_ids(self, value):
        request = self.context.get("request")
        bot = User.objects.get(username="bot@raijin.ai")
        takeaway_types = request.note.project.takeaway_types.filter(
            id__in=value
        ).exclude(takeaways__note=request.note, takeaways__created_by=bot)
        if not takeaway_types:
            raise serializers.ValidationError("No valid takeaway types.")
        return [takeaway_type.id for takeaway_type in takeaway_types]

    def validate(self, attrs):
        request = self.context.get("request")
        if request.note.is_analyzing:
            raise serializers.ValidationError("Report is being analyzed.")
        return super().validate(attrs)

    def create(self, validated_data):
        request = self.context.get("request")
        takeaway_type_ids = validated_data.get("takeaway_type_ids")
        analyze_existing_note.delay(request.note.id, takeaway_type_ids, request.user.id)
        return validated_data
