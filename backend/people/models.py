from django.conf import settings
from django.db import models


class Person(models.Model):
    class RelationshipType(models.TextChoices):
        FAMILY = "family", "Family"
        FRIEND = "friend", "Friend"
        COLLEAGUE = "colleague", "Colleague"
        MANAGER = "manager", "Manager"
        CLIENT = "client", "Client"
        OTHER = "other", "Other"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="people",
    )

    name = models.CharField(
        max_length=200,
    )

    phone_number = models.CharField(
        max_length=30,
        blank=True,
        default="",
    )

    email = models.EmailField(
        blank=True,
        default="",
    )

    relationship = models.CharField(
        max_length=30,
        choices=RelationshipType.choices,
        default=RelationshipType.OTHER,
    )

    notes = models.TextField(
        blank=True,
        default="",
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
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

    class Meta:
        ordering = ["name", "id"]
        indexes = [
            models.Index(fields=["user", "name"]),
            models.Index(fields=["user", "phone_number"]),
            models.Index(fields=["user", "email"]),
            models.Index(fields=["user", "relationship"]),
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return self.name