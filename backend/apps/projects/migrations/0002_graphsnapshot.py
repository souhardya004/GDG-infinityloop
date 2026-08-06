# GraphSnapshot storage for Neo4j-free visualizations

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="GraphSnapshot",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("graph_type", models.CharField(db_index=True, max_length=40)),
                ("payload", models.JSONField(default=dict)),
                ("node_count", models.PositiveIntegerField(default=0)),
                ("edge_count", models.PositiveIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="graphs",
                        to="projects.project",
                    ),
                ),
            ],
            options={"ordering": ["graph_type"]},
        ),
        migrations.AlterUniqueTogether(
            name="graphsnapshot",
            unique_together={("project", "graph_type")},
        ),
    ]
