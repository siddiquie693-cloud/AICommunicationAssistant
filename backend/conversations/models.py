from django.conf import settings
from django.db import models

class Conversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations",
    )

    title = models.CharField(
        max_length=200,
    )

    is_archived = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return self.title

class Message(models.Model):
    SENDER_USER = "user"
    SENDER_ASSISTANT = "assistant"

    SENDER_TYPE_CHOICES = [
        (SENDER_USER, "User"),
        (SENDER_ASSISTANT, "Assistant"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    sender_type = models.CharField(
        max_length=20,
        choices=SENDER_TYPE_CHOICES,
    )

    content = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    ) 

    updated_at = models.DateTimeField(
        auto_now=True,
    ) 

    def __str__(self):
        return f"{self.sender_type}: {self.content[:50]}"  