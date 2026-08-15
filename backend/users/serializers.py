from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.utils import timezone

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
            
                