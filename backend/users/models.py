from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)

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