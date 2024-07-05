from rest_framework import serializers

from api.mixpanel import mixpanel


class MixpanelEventSerializer(serializers.Serializer):
    event_name = serializers.CharField()
    properties = serializers.DictField()

    def create(self, validated_data):
        request = self.context.get("request")
        mixpanel.track(
            request.user.id, validated_data["event_name"], validated_data["properties"]
        )
        return validated_data
