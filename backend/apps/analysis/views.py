"""Job status API."""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analysis.models import AnalysisJob, JobEvent, JobStatus
from apps.analysis.serializers import JobEventSerializer, JobSerializer
from apps.projects.models import Project


class JobDetailView(APIView):
    def get(self, request, project_id, job_id):
        job = get_object_or_404(AnalysisJob, id=job_id, project_id=project_id)
        return Response(JobSerializer(job).data)


class JobEventsView(APIView):
    def get(self, request, project_id, job_id):
        job = get_object_or_404(AnalysisJob, id=job_id, project_id=project_id)
        events = job.events.all()
        return Response(JobEventSerializer(events, many=True).data)


class JobCancelView(APIView):
    def post(self, request, project_id, job_id):
        job = get_object_or_404(AnalysisJob, id=job_id, project_id=project_id)
        if job.status in {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED}:
            return Response(
                {"detail": f"Job already {job.status}."},
                status=status.HTTP_409_CONFLICT,
            )
        if job.celery_task_id:
            from config.celery import app as celery_app

            celery_app.control.revoke(job.celery_task_id, terminate=True)
        from django.utils import timezone

        job.status = JobStatus.CANCELLED
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "finished_at"])
        JobEvent.objects.create(
            job=job,
            stage=job.stage,
            message="Job cancelled by user.",
            level="warn",
        )
        return Response(JobSerializer(job).data)
