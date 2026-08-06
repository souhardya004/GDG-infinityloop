"""Ingest helpers: ZIP extract (zip-slip safe) and GitHub clone."""

from __future__ import annotations

import hashlib
import logging
import shutil
import zipfile
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)


class UnsafeArchiveError(ValueError):
    pass


def project_storage_root(project_id: str) -> Path:
    root = Path(settings.MEDIA_ROOT) / "projects" / str(project_id)
    root.mkdir(parents=True, exist_ok=True)
    return root


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def extract_zip_safely(archive_path: Path, destination: Path) -> Path:
    """Extract ZIP into destination, rejecting zip-slip paths."""
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path, "r") as zf:
        for info in zf.infolist():
            member_path = Path(info.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise UnsafeArchiveError(
                    f"Archive contains unsafe path: {info.filename}"
                )
            target = (destination / member_path).resolve()
            if not str(target).startswith(str(destination.resolve())):
                raise UnsafeArchiveError(
                    f"Archive contains unsafe path: {info.filename}"
                )
        zf.extractall(destination)

    # If ZIP has a single top-level folder, use that as root
    children = [p for p in destination.iterdir() if not p.name.startswith("__MACOSX")]
    if len(children) == 1 and children[0].is_dir():
        return children[0]
    return destination


def clone_github_repo(
    url: str,
    destination: Path,
    *,
    branch: str | None = None,
    commit_sha: str | None = None,
    access_token: str | None = None,
) -> str:
    """Clone a GitHub repository and return the checked-out commit SHA."""
    from git import Repo

    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    clone_url = url
    if access_token and "github.com" in url:
        # https://<token>@github.com/org/repo.git
        cleaned = url.replace("https://", "").replace("http://", "")
        clone_url = f"https://{access_token}@{cleaned}"
        if not clone_url.endswith(".git"):
            clone_url = f"{clone_url.rstrip('/')}.git"

    kwargs: dict = {"url": clone_url, "to_path": str(destination)}
    if branch:
        kwargs["branch"] = branch

    repo = Repo.clone_from(**kwargs)
    if commit_sha:
        repo.git.checkout(commit_sha)
    return repo.head.commit.hexsha
