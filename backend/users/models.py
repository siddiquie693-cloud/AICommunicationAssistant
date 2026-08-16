from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.conf import settings
from django.utils import timezone

class User(AbstractUser):
    email = models.EmailField(unique=True)

    email_verified = models.BooleanField(default=False,)

    email_verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    preferred_language = models.CharField(
        max_length=50,
        default="English",
    )

    voice_language = models.CharField(
        max_length=50,
        default="English",
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