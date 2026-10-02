from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Memory(models.Model):
    class MemoryType(models.TextChoices):
        PREFERENCE = "preference", "Preference"
        FACT = "fact", "Fact"
        RELATIONSHIP = "relationship", "Relationship"
        INSTRUCTION = "instruction", "Instruction"
        GOAL = "goal", "Goal"
        TASK = "task", "Task"
        EVENT = "event", "Event"
        CONTEXT = "context", "Context"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memories",
    )
    content = models.TextField()
    memory_type = models.CharField(
        max_length=32,
        choices=MemoryType.choices,
    )
    importance = models.PositiveSmallIntegerField(
        default=3,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["user", "memory_type"]),
            models.Index(fields=["user", "expires_at"]),
            models.Index(fields=["user", "importance"]),
        ]

    def __str__(self):
        return self.content[:80]