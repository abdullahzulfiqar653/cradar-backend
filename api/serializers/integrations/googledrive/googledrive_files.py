from rest_framework import serializers


class GoogleDriveFileSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    mimeType = serializers.CharField()
    size = serializers.IntegerField(required=False, allow_null=True)
