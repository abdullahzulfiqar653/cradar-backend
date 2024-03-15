# user/serializers.py
from rest_framework import serializers

from api.models.user import User


# User serializer class as nested field in other serializer class
class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(read_only=True)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]


class UserWithWorkspaceOwnerSerializer(UserSerializer):
    is_workspace_owner = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "is_workspace_owner"]


class UsernameSerializer(serializers.ModelSerializer):
    username = serializers.EmailField()

    class Meta:
        model = User
        fields = ["username"]


class UsersSerializer(serializers.Serializer):
    users = UsernameSerializer(many=True)
