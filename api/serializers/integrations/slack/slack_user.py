from rest_framework import serializers

from api.models.integrations.slack.slack_user import SlackUser


class SlackUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlackUser
        fields = "__all__"
