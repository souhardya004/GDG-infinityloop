"""Analysis job tracking."""

from __future__ import annotations

import uuid

from django.db import models

from apps.projects.models import Project


class JobType(models.TextChoices):
    FULL = "full", "Full analysis"
    INCREMENTAL = "incremental", "Incremental"
    REPARSE = "reparse", "Reparse"
    EXPORT = "export", "Export"


class JobStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    RUNNING = "running", "Running"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class JobStage(models.TextChoices):
    QUEUED = "queued", "Queued"
    EXTRACT = "extract", "Extract"
    INVENTORY = "inventory", "Inventory"
    DETECT = "detect", "Detect languages"
    PARSE = "parse", "Parse"
    DEPS = "deps", "Dependencies"
    GRAPH_PERSIST = "graph_persist", "Persist graph"
    FINALIZE = "finalize", "Finalize"
    EXPORT = "export", "Export"


class EventLevel(models.TextChoices):
    INFO = "info", "Info"
    WARN = "warn", "Warn"
    ERROR = "error", "Error"


class AnalysisJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="jobs")
    celery_task_id = models.CharField(max_length=255, blank=True, default="")
    job_type = models.CharField(max_length=20, choices=JobType.choices, default=JobType.FULL)
    status = models.CharField(
        max_length=20, choices=JobStatus.choices, default=JobStatus.QUEUED, db_index=True
    )
    stage = models.CharField(
        max_length=32, choices=JobStage.choices, default=JobStage.QUEUED
    )
    progress_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    error_message = models.TextField(blank=True, default="")
    metrics = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.project_id}:{self.job_type}:{self.status}"


class JobEvent(models.Model):
    job = models.ForeignKey(AnalysisJob, on_delete=models.CASCADE, related_name="events")
    level = models.CharField(max_length=10, choices=EventLevel.choices, default=EventLevel.INFO)
    stage = models.CharField(max_length=32, choices=JobStage.choices)
    message = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
