from rest_framework import serializers


class GoogleDriveOauthUrlSerializer(serializers.Serializer):
    redirect_uri = serializers.URLField(read_only=True)


class GoogleDriveOauthRedirectSerializer(serializers.Serializer):
    state = serializers.CharField()
    code = serializers.CharField()
    project_id = serializers.CharField()
