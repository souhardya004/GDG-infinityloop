# Generated manually for CodeScope bootstrap

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnalysisJob",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("celery_task_id", models.CharField(blank=True, default="", max_length=255)),
                (
                    "job_type",
                    models.CharField(
                        choices=[
                            ("full", "Full analysis"),
                            ("incremental", "Incremental"),
                            ("reparse", "Reparse"),
                            ("export", "Export"),
                        ],
                        default="full",
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("queued", "Queued"),
                            ("running", "Running"),
                            ("succeeded", "Succeeded"),
                            ("failed", "Failed"),
                            ("cancelled", "Cancelled"),
                        ],
                        db_index=True,
                        default="queued",
                        max_length=20,
                    ),
                ),
                (
                    "stage",
                    models.CharField(
                        choices=[
                            ("queued", "Queued"),
                            ("extract", "Extract"),
                            ("inventory", "Inventory"),
                            ("detect", "Detect languages"),
                            ("parse", "Parse"),
                            ("deps", "Dependencies"),
                            ("graph_persist", "Persist graph"),
                            ("finalize", "Finalize"),
                            ("export", "Export"),
                        ],
                        default="queued",
                        max_length=32,
                    ),
                ),
                ("progress_pct", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("error_message", models.TextField(blank=True, default="")),
                ("metrics", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="jobs",
                        to="projects.project",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="JobEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "level",
                    models.CharField(
                        choices=[("info", "Info"), ("warn", "Warn"), ("error", "Error")],
                        default="info",
                        max_length=10,
                    ),
                ),
                (
                    "stage",
                    models.CharField(
                        choices=[
                            ("queued", "Queued"),
                            ("extract", "Extract"),
                            ("inventory", "Inventory"),
                            ("detect", "Detect languages"),
                            ("parse", "Parse"),
                            ("deps", "Dependencies"),
                            ("graph_persist", "Persist graph"),
                            ("finalize", "Finalize"),
                            ("export", "Export"),
                        ],
                        max_length=32,
                    ),
                ),
                ("message", models.TextField()),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "job",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="analysis.analysisjob",
                    ),
                ),
            ],
            options={"ordering": ["created_at"]},
        ),
    ]
