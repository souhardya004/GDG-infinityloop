from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.projects.views import (
    FileTreeView,
    IngestGitHubView,
    IngestZipView,
    ProjectViewSet,
    ReanalyzeView,
)

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "projects/<uuid:project_id>/files/tree/",
        FileTreeView.as_view(),
        name="file-tree",
    ),
    path(
        "projects/<uuid:project_id>/reanalyze/",
        ReanalyzeView.as_view(),
        name="reanalyze",
    ),
    path(
        "projects/<uuid:project_id>/ingest/zip/",
        IngestZipView.as_view(),
        name="ingest-zip",
    ),
    path(
        "projects/<uuid:project_id>/ingest/github/",
        IngestGitHubView.as_view(),
        name="ingest-github",
    ),
]
