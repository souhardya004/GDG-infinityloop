"""Project domain models."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class ProjectStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    INGESTING = "ingesting", "Ingesting"
    ANALYZING = "analyzing", "Analyzing"
    READY = "ready", "Ready"
    FAILED = "failed", "Failed"
    ARCHIVED = "archived", "Archived"


class ProjectVisibility(models.TextChoices):
    PRIVATE = "private", "Private"
    SHARED = "shared", "Shared"
    PUBLIC = "public", "Public"


class SourceType(models.TextChoices):
    ZIP = "zip", "ZIP upload"
    GITHUB = "github", "GitHub"
    GIT_URL = "git_url", "Git URL"
    LOCAL = "local", "Local"


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.DRAFT,
        db_index=True,
    )
    visibility = models.CharField(
        max_length=20,
        choices=ProjectVisibility.choices,
        default=ProjectVisibility.PRIVATE,
    )
    root_path = models.CharField(max_length=1024, blank=True, default="")
    default_branch = models.CharField(max_length=200, blank=True, default="")
    loc_total = models.BigIntegerField(default=0)
    file_count = models.PositiveIntegerField(default=0)
    function_count = models.PositiveIntegerField(default=0)
    class_count = models.PositiveIntegerField(default=0)
    api_count = models.PositiveIntegerField(default=0)
    table_count = models.PositiveIntegerField(default=0)
    technical_debt_score = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    architecture_pattern = models.CharField(max_length=100, blank=True, default="")
    analyzed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("owner", "slug")]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "project"
            candidate = base
            n = 1
            owner = self.owner
            while Project.objects.filter(owner=owner, slug=candidate).exclude(pk=self.pk).exists():
                n += 1
                candidate = f"{base}-{n}"
            self.slug = candidate
        super().save(*args, **kwargs)


class ProjectSource(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="sources")
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    original_filename = models.CharField(max_length=512, blank=True, default="")
    github_url = models.URLField(max_length=500, blank=True, default="")
    git_commit_sha = models.CharField(max_length=64, blank=True, default="")
    archive = models.FileField(upload_to="uploads/%Y/%m/%d/", blank=True, null=True)
    storage_uri = models.CharField(max_length=1024, blank=True, default="")
    checksum_sha256 = models.CharField(max_length=64, blank=True, default="")
    size_bytes = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.project_id}:{self.source_type}"


class ProjectLanguage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="languages")
    language = models.CharField(max_length=64)
    file_count = models.PositiveIntegerField(default=0)
    loc = models.BigIntegerField(default=0)

    class Meta:
        unique_together = [("project", "language")]
        ordering = ["-loc"]

    def __str__(self) -> str:
        return f"{self.project_id}:{self.language}"


class ProjectFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="files")
    relative_path = models.CharField(max_length=1024)
    language = models.CharField(max_length=64, blank=True, default="")
    size_bytes = models.PositiveIntegerField(default=0)
    line_count = models.PositiveIntegerField(default=0)
    content_hash = models.CharField(max_length=64, db_index=True)
    is_generated = models.BooleanField(default=False)
    is_test = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("project", "relative_path")]
        indexes = [
            models.Index(fields=["project", "language"]),
            models.Index(fields=["project", "content_hash"]),
        ]
        ordering = ["relative_path"]

    def __str__(self) -> str:
        return self.relative_path


class GraphSnapshot(models.Model):
    """Persisted visualization graphs so the UI works without Neo4j."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="graphs")
    graph_type = models.CharField(max_length=40, db_index=True)
    payload = models.JSONField(default=dict)
    node_count = models.PositiveIntegerField(default=0)
    edge_count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("project", "graph_type")]
        ordering = ["graph_type"]

    def __str__(self) -> str:
        return f"{self.project_id}:{self.graph_type}"
