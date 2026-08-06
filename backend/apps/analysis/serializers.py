from rest_framework import serializers

from apps.analysis.models import AnalysisJob, JobEvent


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisJob
        fields = (
            "id",
            "project_id",
            "job_type",
            "status",
            "stage",
            "progress_pct",
            "error_message",
            "metrics",
            "celery_task_id",
            "created_at",
            "started_at",
            "finished_at",
        )
        read_only_fields = fields


class JobEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobEvent
        fields = ("id", "job_id", "level", "stage", "message", "payload", "created_at")
        read_only_fields = fields
