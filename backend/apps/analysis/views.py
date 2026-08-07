"""Job status API."""

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analysis.models import AnalysisJob, JobEvent, JobStatus
from apps.analysis.serializers import JobEventSerializer, JobSerializer
from apps.projects.models import Project


def get_job_for_user(job_id: str, project_id: str, user) -> AnalysisJob:
    if not user or not user.is_authenticated:
        raise NotAuthenticated("Authentication required.")
    return get_object_or_404(
        AnalysisJob,
        id=job_id,
        project_id=project_id,
        project__owner=user,
    )


class JobDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id, job_id):
        job = get_job_for_user(job_id, project_id, request.user)
        return Response(JobSerializer(job).data)


class JobEventsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id, job_id):
        job = get_job_for_user(job_id, project_id, request.user)
        events = job.events.all()
        return Response(JobEventSerializer(events, many=True).data)


class JobCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, project_id, job_id):
        job = get_job_for_user(job_id, project_id, request.user)
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
