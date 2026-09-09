from django.conf import settings
from django.db import models

class KnowledgeDocument(models.Model):
    """
    Represents a document that can be used as a knowledge source
    for retrieval-augmented generation.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="knowledge_documents",
    )

    title = models.CharField(
        max_length=255,
    )

    content = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.title    