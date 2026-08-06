"""Celery tasks for analysis pipeline."""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="analysis.run_full_analysis")
def run_full_analysis(
    self,
    job_id: str,
    github_token: str | None = None,
    github_branch: str | None = None,
    github_commit: str | None = None,
) -> dict:
    from apps.analysis.pipeline import AnalysisPipeline

    pipeline = AnalysisPipeline(
        job_id=job_id,
        celery_task_id=self.request.id or "",
        github_token=github_token,
        github_branch=github_branch,
        github_commit=github_commit,
    )
    return pipeline.run()
