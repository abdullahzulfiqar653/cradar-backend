from django.conf import settings
from django.db import models


class SlackUser(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="slack_users"
    )
    access_token = models.CharField(max_length=255)
    slack_user_id = models.CharField(max_length=35)
    slack_team_id = models.CharField(max_length=35)
    bot_user_token = models.CharField(
        max_length=255, blank=True
    )  # Not used now, but stored for future use

    class Meta:
        # since we are using Slack Workspace to identify the SlackUser connection, team_id is used here
        unique_together = (("user", "slack_team_id"),)
