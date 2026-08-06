from django.contrib import admin

from apps.analysis.models import AnalysisJob, JobEvent


@admin.register(AnalysisJob)
class AnalysisJobAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "job_type", "status", "stage", "progress_pct", "created_at")
    list_filter = ("status", "job_type", "stage")


@admin.register(JobEvent)
class JobEventAdmin(admin.ModelAdmin):
    list_display = ("job", "level", "stage", "message", "created_at")
    list_filter = ("level", "stage")
