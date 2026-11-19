import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class PendingConfirmation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        EXPIRED = "expired", "Expired"
        CONSUMED = "consumed", "Consumed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    confirmation_id = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="nira_confirmations",
    )

    action_name = models.CharField(max_length=100)

    parameters = models.JSONField(default=dict)

    reason = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    expires_at = models.DateTimeField(db_index=True)

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "status", "expires_at"],
                name="confirm_user_status_exp_idx",
            ),
        ]

    def is_expired(self):
        return timezone.now() >= self.expires_at