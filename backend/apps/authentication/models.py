from __future__ import annotations

import uuid
from django.conf import settings
from django.db import models


class AuthProvider(models.TextChoices):
    EMAIL = "email", "Email"
    GITHUB = "github", "GitHub"
    GOOGLE = "google", "Google"


class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    avatar_url = models.URLField(max_length=1024, blank=True, default="")
    provider = models.CharField(
        max_length=20,
        choices=AuthProvider.choices,
        default=AuthProvider.EMAIL,
    )
    provider_id = models.CharField(max_length=255, blank=True, default="")
    github_username = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.username} ({self.provider})"
