from django.urls import path

from apps.analysis.views import JobCancelView, JobDetailView, JobEventsView

urlpatterns = [
    path(
        "projects/<uuid:project_id>/jobs/<uuid:job_id>/",
        JobDetailView.as_view(),
        name="job-detail",
    ),
    path(
        "projects/<uuid:project_id>/jobs/<uuid:job_id>/events/",
        JobEventsView.as_view(),
        name="job-events",
    ),
    path(
        "projects/<uuid:project_id>/jobs/<uuid:job_id>/cancel/",
        JobCancelView.as_view(),
        name="job-cancel",
    ),
]
