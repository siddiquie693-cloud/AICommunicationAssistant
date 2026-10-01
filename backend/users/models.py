from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.conf import settings
from django.utils import timezone

class User(AbstractUser):
    email = models.EmailField(unique=True)

    whatsapp_phone_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
    )

    email_verified = models.BooleanField(default=False,)

    email_verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    preferred_language_ref = models.ForeignKey(
        "Language",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preferred_by_users",
    )

    voice_language_ref = models.ForeignKey(
        "Language",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="voice_users",
    )

    timezone = models.CharField(
        max_length=100,
        default="UTC",
    )

    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email

class EmailVerificationToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )

    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    expires_at = models.DateTimeField()

    used = models.BooleanField(
        default=False,
    )

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"Email verification token for {self.user.email}"

class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )

    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    expires_at = models.DateTimeField()

    used = models.BooleanField(
        default=False,
    )

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"Password reset token for {self.user.email}"  

class Language(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    code = models.CharField(
        max_length=10,
        unique=True,
    )

    native_name = models.CharField(
        max_length=100,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.name} ({self.code})"      

class NIRAPersonalProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="nira_personal_profile",
    )
    languages = models.JSONField(
        default=list,
        blank=True,
    )

    communication_style = models.JSONField(
        default=dict,
        blank=True,
    )

    work_info = models.JSONField(
        default=dict,
        blank=True,
    )

    skills = models.JSONField(
        default=list,
        blank=True,
    )

    interests = models.JSONField(
        default=list,
        blank=True,
    )

    important_people = models.JSONField(
        default=list,
        blank=True,
    )

    custom_instructions = models.TextField(
        blank=True,
        default="",
    )

    privacy_settings = models.JSONField(
        default=dict,
        blank=True,
    )

    memory_settings = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def clean(self):
        from django.core.exceptions import ValidationError

        list_fields = {
            "languages",
            "skills",
            "interests",
            "important_people",
        }

        dict_fields = {
            "communication_style",
            "work_info",
            "privacy_settings",
            "memory_settings",
        }

        errors = {}

        for field_name in list_fields:
            value = getattr(self, field_name)

            if not isinstance(value, list):
                errors[field_name] = "This field must contain a list."

        for field_name in dict_fields:
            value = getattr(self, field_name)

            if not isinstance(value, dict):
                errors[field_name] = "This field must contain an object."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"NIRA Personal Profile for {self.user.email}"    