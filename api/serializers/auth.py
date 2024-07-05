from datetime import datetime

import requests
from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import update_last_login
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from rest_framework import exceptions, serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
    api_settings,
)
from rest_framework_simplejwt.tokens import RefreshToken

from api.mixpanel import mixpanel
from api.models.invitation import Invitation
from api.models.user import User
from api.serializers.project import ProjectSerializer
from api.serializers.user import UserSerializer
from api.serializers.workspace import WorkspaceSerializer


def create_mixpanel_user(user):
    mixpanel.people_set(
        user.id,
        {
            "$email": user.email,
            "$first_name": user.first_name,
            "$last_name": user.last_name,
            "$created": user.date_joined,
        },
    )


class SignupSerializer(serializers.Serializer):
    username = serializers.EmailField()
    first_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        # TODO: update var to email instead
        fields = ["username", "first_name", "last_name", "password", "workspace_name"]

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def validate_username(self, value):
        username = value
        if username and User.objects.filter(username__iexact=username).exists():
            raise exceptions.ValidationError(f"User {username} already exists.")
        return value.lower()

    def create(self, validated_data):
        # Create user
        user = User(
            email=validated_data.get("username"),
            username=validated_data.get("username"),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        user.set_password(validated_data.get("password"))
        user.save()
        create_mixpanel_user(user)

        return user


class GoogleLoginSerializer(serializers.Serializer):
    google_access_token = serializers.CharField(write_only=True)
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

    def get_user_info(self, google_access_token):
        google_response = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {google_access_token}"},
        )
        if google_response.status_code == 401:
            raise exceptions.AuthenticationFailed(
                "Failed to authenticate google access token."
            )
        user_info = google_response.json()
        return user_info

    def create(self, validated_data):
        # Get user info from Google
        google_access_token = validated_data.get("google_access_token")
        user_info = self.get_user_info(google_access_token)

        # Get or create user
        user, created = User.objects.get_or_create(
            username__iexact=user_info.get("email").lower(),
            defaults={
                "username": user_info.get("email").lower(),
                "first_name": user_info.get("given_name"),
                "last_name": user_info.get("family_name"),
                "email": user_info.get("email"),
            },
        )
        if created:
            user.set_unusable_password()
            user.save()
            create_mixpanel_user(user)

        # Generate access and refresh token
        refresh = RefreshToken.for_user(user)
        data = {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }

        update_last_login(None, user)
        return data


class PasswordUpdateSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        request = kwargs.get("context").get("request")
        if request is not None and hasattr(request, "user"):
            self.user = request.user
        super().__init__(*args, **kwargs)

    def validate_old_password(self, value):
        if not self.user.check_password(value):
            raise exceptions.ValidationError(
                "Your old password was entered incorrectly. Please enter it again."
            )
        return value

    def validate_password(self, value):
        password_validation.validate_password(value, self.user)
        return value

    def create(self, validated_data):
        password = validated_data["password"]
        self.user.set_password(password)
        self.user.save()
        return self.user


class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        self.form = PasswordResetForm(data)
        if self.form.is_valid():
            return self.form.cleaned_data
        raise exceptions.ValidationError(self.form.errors)

    def create(self, validated_data):
        request = self.context["request"]
        self.form.save(
            request=request,
            email_template_name="password_reset_email.html",
            extra_email_context={
                "frontend_url": settings.FRONTEND_URL,
            },
        )
        return validated_data


class DoPasswordResetSerializer(serializers.Serializer):
    # Ref: django.contrib.auth.views.PasswordResetConfirmView
    uidb64 = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    token_generator = default_token_generator

    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            ValidationError,
        ):
            user = None
        return user

    def validate(self, data):
        self.user = self.get_user(data["uidb64"])
        if self.user is None:
            raise exceptions.ValidationError("Password reset unsuccessful.")
        password = data["password"]
        token = data["token"]
        if not self.token_generator.check_token(self.user, token):
            raise exceptions.ValidationError("Password reset unsuccessful.")
        password_validation.validate_password(password, self.user)
        return data

    def create(self, validated_data):
        password = validated_data["password"]
        self.user.set_password(password)
        self.user.save()
        return validated_data


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["access_token"] = data.pop("access")
        data["refresh_token"] = data.pop("refresh")
        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    refresh = None
    access = None
    refresh_token = serializers.CharField()
    access_token = serializers.CharField(read_only=True)

    def validate(self, attrs):
        attrs["refresh"] = attrs.pop("refresh_token")
        data = super().validate(attrs)
        data["access_token"] = data.pop("access")
        data["refresh_token"] = data.pop("refresh")
        if api_settings.UPDATE_LAST_LOGIN:
            refresh_token = RefreshToken(data["refresh_token"], verify=False)
            user_id = refresh_token.payload["user_id"]
            user = User.objects.get(pk=user_id)
            update_last_login(None, user)
        return data


class InviteUserSerializer(serializers.Serializer):
    emails = serializers.ListField(child=serializers.EmailField(), allow_empty=False)


class InvitationStatusSerializer(serializers.ModelSerializer):
    is_signed_up = serializers.BooleanField()
    email = serializers.EmailField(source="recipient_email")
    workspace = WorkspaceSerializer(read_only=True)
    project = ProjectSerializer(read_only=True)
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Invitation
        fields = ["is_signed_up", "email", "workspace", "project", "sender"]

    def to_serializer_error(self, exc):
        return exceptions.ValidationError(detail=serializers.as_serializer_error(exc))

    def validate_invitation(self, invitation: Invitation):
        if timezone.make_aware(datetime.now()) > invitation.expires_at:
            exception = exceptions.ValidationError("Token has expired.")
            raise self.to_serializer_error(exception)

        if invitation.is_used:
            exception = exceptions.ValidationError("Token has been used.")
            raise self.to_serializer_error(exception)

    def to_representation(self, invitation: Invitation):
        request = self.context["request"]
        self.validate_invitation(invitation)
        user = User.objects.filter(username__iexact=invitation.recipient_email).first()

        if user is None:
            invitation.is_signed_up = False

        elif request.user == user:
            invitation.is_signed_up = True
            request.user.workspaces.add(invitation.workspace)
            request.user.projects.add(invitation.project)
            invitation.is_used = True
            invitation.save()

        else:
            err_message = (
                f"The email {invitation.recipient_email} has already been taken. "
                "If you are the account owner, please login and click on the invitation link again."
            )
            exception = exceptions.ValidationError(err_message)
            raise self.to_serializer_error(exception)

        return super().to_representation(invitation)


class InvitationSignupSerializer(SignupSerializer):
    username = None
    token = serializers.CharField()
    workspace = WorkspaceSerializer(read_only=True)
    project = ProjectSerializer(read_only=True)

    def validate(self, data):
        # Get invitation
        token = data.get("token")
        self.invitation = invitation = get_object_or_404(Invitation, token=token)
        if timezone.make_aware(datetime.now()) > invitation.expires_at:
            raise exceptions.ValidationError("Token has expired.")

        if invitation.is_used:
            raise exceptions.ValidationError("Token has been used.")

        if User.objects.filter(username__iexact=invitation.recipient_email):
            raise exceptions.ValidationError(
                f"Email {invitation.recipient_email} has already been taken."
            )

        return data

    def create(self, validated_data):
        invitation = self.invitation

        # Create user, add workspace and add project
        validated_data["username"] = invitation.recipient_email.lower()
        validated_data["workspace"] = invitation.workspace
        # Calling SignupSerializer.create method
        user = super().create(validated_data)
        create_mixpanel_user(user)
        user.workspaces.add(invitation.workspace)
        user.projects.add(invitation.project)

        # Update invitation
        invitation.created_user = user
        invitation.is_used = True
        invitation.save()

        # Return project_id
        validated_data["workspace"] = invitation.workspace
        validated_data["project"] = invitation.project
        return validated_data
