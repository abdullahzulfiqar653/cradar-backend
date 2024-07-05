from rest_framework import serializers

from api.ai.generators.note_message_generator import generate_message
from api.models.message import Message
from api.models.user import User
from api.serializers.user import UserSerializer


class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Message
        exclude = ["note"]
        # Only text is allowed to be set
        read_only_fields = [
            "id",
            "role",
            "user",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["role"] = Message.Role.HUMAN
        validated_data["user"] = request.user
        validated_data["note"] = request.note
        super().create(validated_data)
        output = generate_message(request.note, request.user)
        bot = User.objects.get(email="bot@raijin.ai")
        ai_message = Message.objects.create(
            note=request.note,
            role=Message.Role.AI,
            user=bot,
            text=output,
        )
        return ai_message
