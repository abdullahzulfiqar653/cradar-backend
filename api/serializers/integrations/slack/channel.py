from rest_framework import serializers


class SlackChannelSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    context_team_id = serializers.CharField()
    is_member = serializers.BooleanField()


class ListChannelsSerializer(serializers.Serializer):
    channels = SlackChannelSerializer(many=True, read_only=True)
