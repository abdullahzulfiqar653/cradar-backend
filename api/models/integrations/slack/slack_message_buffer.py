from django.db import models


class SlackMessageBuffer(models.Model):
    slack_channel_id = models.CharField(max_length=25)
    slack_team_id = models.CharField(max_length=25)
    slack_user = models.CharField(
        max_length=25
    )  # This can be slack user name, fallback to slack user id if not available
    message_text = models.TextField()
    timestamp = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["slack_channel_id", "slack_team_id"]),
        ]
