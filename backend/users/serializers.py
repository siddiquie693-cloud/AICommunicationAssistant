from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.utils import timezone
from .models import (
    PasswordResetToken,
    Language,
)
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "preferred_language",
            "voice_language",
            "timezone",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.token = RefreshToken(attrs["refresh"])
        return attrs

    def save(self, **kwargs):
        self.token.blacklist()

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "preferred_language",
            "voice_language",
            "timezone",
        ]
        read_only_fields = [
            "id",
            "username",
            "email",
        ]

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True,
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    def validate(self, attrs):
        user = self.context["request"].user

        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError(
                {
                    "old_password": "Current password is incorrect."
                }
            )
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {
                    "new_password": (
                        "New password must be different"
                        "from the current password."
                    )
                }
            )
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])

        return user

class EmailVerificationTokenSerializer(serializers.Serializer):
    def create_token(self, user):
        EmailVerificationToken = user.email_verification_tokens.model

        EmailVerificationToken.objects.filter(
            user=user,
            used=False,
        ).update(
            used=True,
        )

        token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(minutes=30),
        )

        return token

class EmailVerificayionSerializer(serializers.Serializer):
    token = serializers.UUIDField()

    def validate_token(self, value):
        from .models import EmailVerificationToken

        try:
            verification_token = EmailVerificationToken.objects.select_related(
                "user"
            ).get(token=value)
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid verification token."
            )

        if verification_token.used:
            raise serializers.ValidationError(
                "Verification token has already been used."
            )

        if verification_token.is_expired():
            raise serializers.ValidationError(
                "Verification token has expired."
            )

        self.verification_token = verification_token

        return value

class PasswordResetTokenSerializer(serializers.Serializer):
    def create_token(self, user):
        PasswordResetToken = user.password_reset_tokens.model

        PasswordResetToken.objects.filter(
            user=user,
            used=False,
        ).update(
            used=True,
        )

        token =PasswordResetToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(minutes=30),
        )
        return token

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    def validate(self, attrs):
        token_value = attrs["token"]

        try:
            reset_token = PasswordResetToken.objects.select_related(
                "user"
            ).get(token=token_value)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "token": "Invalid password reset token."
                }
            )

        if reset_token.used:
            raise serializers.ValidationError(
                {
                    "token": "Password reset token has already been used."
                }
            )

        if reset_token.is_expired():
            raise serializers.ValidationError(
                {
                    "token": "Password reset token has expired."
                }
            )
        attrs["reset_token"] = reset_token

        return attrs

    def save(self):
        reset_token = self.validated_data["reset_token"]
        new_password = self.validated_data["new_password"]

        user = reset_token.user

        user.set_password(new_password)
        user.save(update_fields=["password"])

        reset_token.used =True
        reset_token.save(update_fields=["used"])

        return user

class UserLoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        if not self.user.email_verified:
            raise serializers.ValidationError(
                {
                    "email": (
                        "Please verify your email address "
                        "before logging in."
                    )
                }
            )
        return data 

class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        from .models import User

        user = User.objects.filter(
            email=value,
            is_active=True,
        ).first()

        if user and user.email_verified:
            raise serializers.ValidationError(
                "Email address is already verified."
            )

        self.user = user

        return value

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = [
            "id",
            "name",
            "code",
            "native_name",
        ]
