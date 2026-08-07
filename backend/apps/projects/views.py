"""Project and ingest API views."""

from __future__ import annotations

import logging
from pathlib import Path

from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analysis.models import AnalysisJob, JobStatus, JobType
from apps.analysis.serializers import JobSerializer
from apps.analysis.tasks import run_full_analysis
from apps.projects.models import Project, ProjectSource, ProjectStatus, SourceType
from apps.projects.serializers import (
    IngestGitHubSerializer,
    ProjectCreateSerializer,
    ProjectFileSerializer,
    ProjectSerializer,
    ProjectSourceSerializer,
    ProjectSummarySerializer,
    ProjectUpdateSerializer,
)
from apps.projects.services.ingest import project_storage_root, sha256_file
from apps.projects.services.tree import build_file_tree

logger = logging.getLogger(__name__)


class ProjectViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    lookup_field = "id"
    search_fields = ("name", "description", "slug")
    filterset_fields = ("status", "visibility")
    ordering_fields = ("created_at", "name", "loc_total", "file_count")

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Project.objects.filter(owner=self.request.user).prefetch_related("languages")
        return Project.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return ProjectCreateSerializer
        if self.action in {"update", "partial_update"}:
            return ProjectUpdateSerializer
        if self.action == "list":
            return ProjectSummarySerializer
        return ProjectSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        project = serializer.instance
        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance: Project):
        instance.status = ProjectStatus.ARCHIVED
        instance.save(update_fields=["status", "updated_at"])


class FileTreeView(APIView):
    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id, owner=request.user)
        return Response(
            {
                "project_id": str(project.id),
                "file_count": project.files.count(),
                "tree": build_file_tree(project.id),
            }
        )


class ReanalyzeView(APIView):
    """Re-run analysis for an existing project source."""

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id, owner=request.user)
        if not project.sources.exists() and not project.root_path:
            return Response(
                {"detail": "No source available to re-analyze."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        project.status = ProjectStatus.ANALYZING
        project.save(update_fields=["status", "updated_at"])
        job = AnalysisJob.objects.create(
            project=project,
            job_type=JobType.FULL,
            status=JobStatus.QUEUED,
        )
        _enqueue_analysis(job)
        return Response(JobSerializer(job).data, status=status.HTTP_202_ACCEPTED)


class IngestZipView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id, owner=request.user)
        upload = request.FILES.get("file")
        if upload is None:
            return Response(
                {"detail": "Missing multipart field 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not upload.name.lower().endswith(".zip"):
            return Response(
                {"detail": "Only .zip archives are supported."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        source = ProjectSource.objects.create(
            project=project,
            source_type=SourceType.ZIP,
            original_filename=upload.name,
            archive=upload,
            size_bytes=upload.size,
        )
        if source.archive:
            path = Path(source.archive.path)
            source.checksum_sha256 = sha256_file(path)
            source.storage_uri = str(path)
            source.save(update_fields=["checksum_sha256", "storage_uri"])

        project.status = ProjectStatus.INGESTING
        project.root_path = str(project_storage_root(str(project.id)) / "src")
        project.save(update_fields=["status", "root_path", "updated_at"])

        job = AnalysisJob.objects.create(
            project=project,
            job_type=JobType.FULL,
            status=JobStatus.QUEUED,
        )
        _enqueue_analysis(job)

        return Response(
            {
                "source": ProjectSourceSerializer(source).data,
                "job": JobSerializer(job).data,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class IngestGitHubView(APIView):
    parser_classes = [JSONParser]

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id, owner=request.user)
        serializer = IngestGitHubSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        source = ProjectSource.objects.create(
            project=project,
            source_type=SourceType.GITHUB,
            github_url=data["url"],
            git_commit_sha=data.get("commit_sha") or "",
        )

        project.status = ProjectStatus.INGESTING
        project.root_path = str(project_storage_root(str(project.id)) / "src")
        project.default_branch = data.get("branch") or ""
        project.save(update_fields=["status", "root_path", "default_branch", "updated_at"])

        job = AnalysisJob.objects.create(
            project=project,
            job_type=JobType.FULL,
            status=JobStatus.QUEUED,
            metrics={"ingest": {"access_token_provided": bool(data.get("access_token"))}},
        )
        _enqueue_analysis(
            job,
            github_token=data.get("access_token") or None,
            github_branch=data.get("branch") or None,
            github_commit=data.get("commit_sha") or None,
        )

        return Response(
            {
                "source": ProjectSourceSerializer(source).data,
                "job": JobSerializer(job).data,
            },
            status=status.HTTP_202_ACCEPTED,
        )


def _enqueue_analysis(job: AnalysisJob, **kwargs) -> None:
    from django.conf import settings

    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
        logger.info("CELERY_TASK_ALWAYS_EAGER is True; executing analysis synchronously.")
        from apps.analysis.pipeline import AnalysisPipeline

        AnalysisPipeline(job_id=str(job.id), **kwargs).run()
        job.refresh_from_db()
        return

    try:
        async_result = run_full_analysis.delay(str(job.id), **kwargs)
        job.celery_task_id = getattr(async_result, "id", "") or ""
        job.save(update_fields=["celery_task_id"])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Celery unavailable (%s); running analysis synchronously.", exc)
        from apps.analysis.pipeline import AnalysisPipeline

        AnalysisPipeline(job_id=str(job.id), **kwargs).run()
        job.refresh_from_db()
