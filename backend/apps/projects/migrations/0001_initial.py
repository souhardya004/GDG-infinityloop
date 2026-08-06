# Generated manually for CodeScope bootstrap

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=220)),
                ("description", models.TextField(blank=True, default="")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("ingesting", "Ingesting"),
                            ("analyzing", "Analyzing"),
                            ("ready", "Ready"),
                            ("failed", "Failed"),
                            ("archived", "Archived"),
                        ],
                        db_index=True,
                        default="draft",
                        max_length=20,
                    ),
                ),
                (
                    "visibility",
                    models.CharField(
                        choices=[
                            ("private", "Private"),
                            ("shared", "Shared"),
                            ("public", "Public"),
                        ],
                        default="private",
                        max_length=20,
                    ),
                ),
                ("root_path", models.CharField(blank=True, default="", max_length=1024)),
                ("default_branch", models.CharField(blank=True, default="", max_length=200)),
                ("loc_total", models.BigIntegerField(default=0)),
                ("file_count", models.PositiveIntegerField(default=0)),
                ("function_count", models.PositiveIntegerField(default=0)),
                ("class_count", models.PositiveIntegerField(default=0)),
                ("api_count", models.PositiveIntegerField(default=0)),
                ("table_count", models.PositiveIntegerField(default=0)),
                (
                    "technical_debt_score",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
                ),
                ("architecture_pattern", models.CharField(blank=True, default="", max_length=100)),
                ("analyzed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="projects",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ProjectFile",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("relative_path", models.CharField(max_length=1024)),
                ("language", models.CharField(blank=True, default="", max_length=64)),
                ("size_bytes", models.PositiveIntegerField(default=0)),
                ("line_count", models.PositiveIntegerField(default=0)),
                ("content_hash", models.CharField(db_index=True, max_length=64)),
                ("is_generated", models.BooleanField(default=False)),
                ("is_test", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="files",
                        to="projects.project",
                    ),
                ),
            ],
            options={"ordering": ["relative_path"]},
        ),
        migrations.CreateModel(
            name="ProjectLanguage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("language", models.CharField(max_length=64)),
                ("file_count", models.PositiveIntegerField(default=0)),
                ("loc", models.BigIntegerField(default=0)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="languages",
                        to="projects.project",
                    ),
                ),
            ],
            options={"ordering": ["-loc"]},
        ),
        migrations.CreateModel(
            name="ProjectSource",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "source_type",
                    models.CharField(
                        choices=[
                            ("zip", "ZIP upload"),
                            ("github", "GitHub"),
                            ("git_url", "Git URL"),
                            ("local", "Local"),
                        ],
                        max_length=20,
                    ),
                ),
                ("original_filename", models.CharField(blank=True, default="", max_length=512)),
                ("github_url", models.URLField(blank=True, default="", max_length=500)),
                ("git_commit_sha", models.CharField(blank=True, default="", max_length=64)),
                ("archive", models.FileField(blank=True, null=True, upload_to="uploads/%Y/%m/%d/")),
                ("storage_uri", models.CharField(blank=True, default="", max_length=1024)),
                ("checksum_sha256", models.CharField(blank=True, default="", max_length=64)),
                ("size_bytes", models.BigIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sources",
                        to="projects.project",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="project",
            index=models.Index(fields=["status", "-created_at"], name="projects_pr_status_7c0a8f_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="project",
            unique_together={("owner", "slug")},
        ),
        migrations.AddIndex(
            model_name="projectfile",
            index=models.Index(fields=["project", "language"], name="projects_pr_project_6b4f2a_idx"),
        ),
        migrations.AddIndex(
            model_name="projectfile",
            index=models.Index(fields=["project", "content_hash"], name="projects_pr_project_9e1d3c_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="projectfile",
            unique_together={("project", "relative_path")},
        ),
        migrations.AlterUniqueTogether(
            name="projectlanguage",
            unique_together={("project", "language")},
        ),
    ]
