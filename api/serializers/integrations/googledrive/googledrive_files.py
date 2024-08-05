from rest_framework import serializers


class GoogleDriveFileSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    mimeType = serializers.CharField()
    size = serializers.IntegerField(required=False, allow_null=True)

    def validate_mimeType(self, value):
        allowed_mime_types = [
            "application/vnd.google-apps.document",
            "application/pdf",
            "audio/mpeg",  # mp3
            "video/mp4",  # mp4
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
            "text/plain",  # txt
            "audio/wav",  # wav
        ]
        if value not in allowed_mime_types:
            raise serializers.ValidationError("Invalid mimeType")
        return value
