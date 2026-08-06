"""Full analysis pipeline: extract → inventory → parse → graph → finalize."""

from __future__ import annotations

import hashlib
import logging
from collections import Counter
from pathlib import Path

from django.utils import timezone as dj_timezone

from apps.analysis.models import AnalysisJob, EventLevel, JobEvent, JobStage, JobStatus
from apps.core.languages import detect_language, is_probably_generated, is_probably_test
from apps.graphs.services.neo4j_client import Neo4jGraphStore
from apps.parsers.registry import ParserRegistry
from apps.projects.models import (
    Project,
    ProjectFile,
    ProjectLanguage,
    ProjectStatus,
    SourceType,
)
from apps.projects.services.ingest import (
    UnsafeArchiveError,
    clone_github_repo,
    extract_zip_safely,
    project_storage_root,
)

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    def __init__(
        self,
        job_id: str,
        *,
        celery_task_id: str = "",
        github_token: str | None = None,
        github_branch: str | None = None,
        github_commit: str | None = None,
    ) -> None:
        self.job = AnalysisJob.objects.select_related("project").get(id=job_id)
        self.project: Project = self.job.project
        self.celery_task_id = celery_task_id
        self.github_token = github_token
        self.github_branch = github_branch
        self.github_commit = github_commit
        self.registry = ParserRegistry.default()
        self.metrics: dict = {}

    def run(self) -> dict:
        try:
            self._mark_running()
            root = self._extract()
            self._inventory(root)
            parse_result = self._parse(root)
            self._persist_graph(parse_result)
            self._finalize()
            return {"job_id": str(self.job.id), "status": "succeeded", "metrics": self.metrics}
        except Exception as exc:  # noqa: BLE001
            logger.exception("Analysis failed for job %s", self.job.id)
            self._fail(str(exc))
            return {"job_id": str(self.job.id), "status": "failed", "error": str(exc)}

    def _mark_running(self) -> None:
        self.job.status = JobStatus.RUNNING
        self.job.started_at = dj_timezone.now()
        if self.celery_task_id:
            self.job.celery_task_id = self.celery_task_id
        self.job.save(update_fields=["status", "started_at", "celery_task_id"])
        self.project.status = ProjectStatus.ANALYZING
        self.project.save(update_fields=["status", "updated_at"])
        self._event(JobStage.QUEUED, "Analysis started.")

    def _extract(self) -> Path:
        self._update_stage(JobStage.EXTRACT, 5, "Extracting / cloning source…")
        source = (
            self.project.sources.order_by("-created_at").first()
        )
        if source is None:
            raise RuntimeError("No project source found.")

        dest = project_storage_root(str(self.project.id)) / "src"
        if source.source_type == SourceType.ZIP:
            if not source.archive:
                raise RuntimeError("ZIP source missing archive file.")
            archive_path = Path(source.archive.path)
            try:
                root = extract_zip_safely(archive_path, dest)
            except UnsafeArchiveError as exc:
                raise RuntimeError(str(exc)) from exc
        elif source.source_type == SourceType.GITHUB:
            sha = clone_github_repo(
                source.github_url,
                dest,
                branch=self.github_branch or self.project.default_branch or None,
                commit_sha=self.github_commit or source.git_commit_sha or None,
                access_token=self.github_token,
            )
            source.git_commit_sha = sha
            source.save(update_fields=["git_commit_sha"])
            root = dest
        else:
            raise RuntimeError(f"Unsupported source type: {source.source_type}")

        self.project.root_path = str(root)
        self.project.save(update_fields=["root_path", "updated_at"])
        self.metrics["root"] = str(root)
        self._event(JobStage.EXTRACT, f"Source ready at {root}")
        return Path(root)

    def _inventory(self, root: Path) -> None:
        self._update_stage(JobStage.INVENTORY, 20, "Inventorying files…")
        ProjectFile.objects.filter(project=self.project).delete()
        ProjectLanguage.objects.filter(project=self.project).delete()

        rows: list[ProjectFile] = []
        lang_files: Counter[str] = Counter()
        lang_loc: Counter[str] = Counter()
        total_loc = 0
        skip_dirs = {
            ".git",
            "node_modules",
            "__pycache__",
            ".venv",
            "venv",
            "dist",
            "build",
            ".next",
            "target",
            "vendor",
        }

        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in skip_dirs for part in path.parts):
                continue
            rel = path.relative_to(root).as_posix()
            if is_probably_generated(rel):
                continue
            try:
                data = path.read_bytes()
            except OSError:
                continue
            if b"\x00" in data[:1024]:
                continue  # binary
            text = data.decode("utf-8", errors="replace")
            lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
            language = detect_language(rel) or ""
            content_hash = hashlib.sha256(data).hexdigest()
            rows.append(
                ProjectFile(
                    project=self.project,
                    relative_path=rel,
                    language=language,
                    size_bytes=len(data),
                    line_count=lines,
                    content_hash=content_hash,
                    is_test=is_probably_test(rel),
                    is_generated=False,
                )
            )
            total_loc += lines
            if language:
                lang_files[language] += 1
                lang_loc[language] += lines

        ProjectFile.objects.bulk_create(rows, batch_size=500)
        ProjectLanguage.objects.bulk_create(
            [
                ProjectLanguage(
                    project=self.project,
                    language=lang,
                    file_count=lang_files[lang],
                    loc=lang_loc[lang],
                )
                for lang in lang_files
            ]
        )
        self.project.file_count = len(rows)
        self.project.loc_total = total_loc
        self.project.save(update_fields=["file_count", "loc_total", "updated_at"])
        self.metrics["file_count"] = len(rows)
        self.metrics["loc_total"] = total_loc
        self._update_stage(JobStage.DETECT, 35, f"Detected {len(lang_files)} languages.")
        self._event(
            JobStage.DETECT,
            "Language inventory complete.",
            payload={"languages": dict(lang_files)},
        )

    def _parse(self, root: Path) -> dict:
        self._update_stage(JobStage.PARSE, 50, "Parsing source files…")
        files = ProjectFile.objects.filter(project=self.project).exclude(language="")
        nodes: list[dict] = []
        edges: list[dict] = []
        function_count = 0
        class_count = 0
        parsed = 0

        # Always include folder/file nodes for folder + file dependency graphs
        for pf in ProjectFile.objects.filter(project=self.project):
            file_uid = f"file:{pf.relative_path}"
            nodes.append(
                {
                    "uid": file_uid,
                    "labels": ["File"],
                    "properties": {
                        "path": pf.relative_path,
                        "language": pf.language,
                        "loc": pf.line_count,
                        "project_id": str(self.project.id),
                    },
                }
            )
            # folder containment
            parts = pf.relative_path.split("/")
            parent = ""
            for i, part in enumerate(parts[:-1]):
                folder_path = "/".join(parts[: i + 1])
                folder_uid = f"folder:{folder_path}"
                nodes.append(
                    {
                        "uid": folder_uid,
                        "labels": ["Folder"],
                        "properties": {
                            "path": folder_path,
                            "name": part,
                            "project_id": str(self.project.id),
                        },
                    }
                )
                child_uid = (
                    f"folder:{'/'.join(parts[: i + 2])}"
                    if i < len(parts) - 2
                    else file_uid
                )
                if i == len(parts) - 2:
                    child_uid = file_uid
                else:
                    child_uid = f"folder:{'/'.join(parts[: i + 2])}"
                edges.append(
                    {
                        "type": "CONTAINS",
                        "source_uid": folder_uid,
                        "target_uid": child_uid,
                        "properties": {"project_id": str(self.project.id)},
                    }
                )
                parent = folder_path

        for pf in files.iterator():
            path = root / pf.relative_path
            if not path.exists():
                continue
            plugin = self.registry.resolve(pf.relative_path, pf.language)
            if plugin is None:
                continue
            try:
                source = path.read_bytes()
                ir = plugin.parse(pf.relative_path, source)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Parse failed for %s: %s", pf.relative_path, exc)
                self._event(
                    JobStage.PARSE,
                    f"Parse failed: {pf.relative_path}",
                    level=EventLevel.WARN,
                    payload={"error": str(exc)},
                )
                continue

            parsed += 1
            file_uid = f"file:{pf.relative_path}"
            for symbol in ir.symbols:
                labels = ["Symbol"]
                if symbol.kind == "function":
                    labels.append("Function")
                    function_count += 1
                elif symbol.kind == "class":
                    labels.append("Class")
                    class_count += 1
                elif symbol.kind == "method":
                    labels.append("Method")
                uid = f"{symbol.kind[:2]}:{symbol.qualified_name}"
                nodes.append(
                    {
                        "uid": uid,
                        "labels": labels,
                        "properties": {
                            "name": symbol.name,
                            "kind": symbol.kind,
                            "qualified_name": symbol.qualified_name,
                            "line_start": symbol.line_start,
                            "line_end": symbol.line_end,
                            "docstring": symbol.docstring or "",
                            "return_type": symbol.return_type or "",
                            "is_async": symbol.is_async,
                            "project_id": str(self.project.id),
                            "file_path": pf.relative_path,
                        },
                    }
                )
                edges.append(
                    {
                        "type": "DECLARES",
                        "source_uid": file_uid,
                        "target_uid": uid,
                        "properties": {
                            "line": symbol.line_start,
                            "project_id": str(self.project.id),
                        },
                    }
                )
                for base in symbol.bases:
                    base_uid = f"cl:{base}"
                    edges.append(
                        {
                            "type": "INHERITS",
                            "source_uid": uid,
                            "target_uid": base_uid,
                            "properties": {
                                "project_id": str(self.project.id),
                                "resolved": False,
                            },
                        }
                    )
                    nodes.append(
                        {
                            "uid": base_uid,
                            "labels": ["Class", "Symbol"],
                            "properties": {
                                "name": base,
                                "kind": "class",
                                "qualified_name": base,
                                "project_id": str(self.project.id),
                            },
                        }
                    )
                for call in symbol.calls:
                    callee_uid = f"fn:{call.callee}"
                    edges.append(
                        {
                            "type": "CALLS",
                            "source_uid": uid,
                            "target_uid": callee_uid,
                            "properties": {
                                "line": call.line,
                                "is_await": call.is_await,
                                "project_id": str(self.project.id),
                                "resolved": False,
                            },
                        }
                    )
                    nodes.append(
                        {
                            "uid": callee_uid,
                            "labels": ["Function", "Symbol"],
                            "properties": {
                                "name": call.callee,
                                "kind": "function",
                                "qualified_name": call.callee,
                                "project_id": str(self.project.id),
                            },
                        }
                    )

            for imp in ir.imports:
                target = (
                    f"file:{imp.resolved_path}"
                    if imp.resolved_path
                    else f"mod:{imp.module}"
                )
                edges.append(
                    {
                        "type": "IMPORTS",
                        "source_uid": file_uid,
                        "target_uid": target,
                        "properties": {
                            "names": imp.names,
                            "line": imp.line,
                            "project_id": str(self.project.id),
                        },
                    }
                )
                nodes.append(
                    {
                        "uid": target,
                        "labels": ["Module"] if target.startswith("mod:") else ["File"],
                        "properties": {
                            "name": imp.module,
                            "project_id": str(self.project.id),
                        },
                    }
                )

        self.project.function_count = function_count
        self.project.class_count = class_count
        self.project.save(update_fields=["function_count", "class_count", "updated_at"])
        self.metrics["parsed_files"] = parsed
        self.metrics["function_count"] = function_count
        self.metrics["class_count"] = class_count
        self._update_stage(JobStage.DEPS, 70, f"Parsed {parsed} files.")
        return {"nodes": nodes, "edges": edges}

    def _persist_graph(self, fragment: dict) -> None:
        self._update_stage(JobStage.GRAPH_PERSIST, 85, "Persisting architecture graphs…")
        from apps.graphs.services.snapshots import save_snapshots

        counts = save_snapshots(self.project, fragment)
        self.metrics["graph_nodes"] = {k: v for k, v in counts.items()}
        self._event(
            JobStage.GRAPH_PERSIST,
            f"Saved Postgres graph snapshots: {sum(counts.values())} nodes across {len(counts)} views.",
        )

        store = Neo4jGraphStore()
        try:
            store.replace_project_graph(
                str(self.project.id),
                fragment["nodes"],
                fragment["edges"],
            )
            self._event(
                JobStage.GRAPH_PERSIST,
                f"Also wrote {len(fragment['nodes'])} nodes to Neo4j.",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Neo4j persist skipped: %s", exc)
            self._event(
                JobStage.GRAPH_PERSIST,
                f"Neo4j unavailable (OK — Postgres snapshots are primary): {exc}",
                level=EventLevel.WARN,
            )
            self.metrics["neo4j"] = "skipped"
        finally:
            try:
                store.close()
            except Exception:  # noqa: BLE001
                pass

    def _finalize(self) -> None:
        self._update_stage(JobStage.FINALIZE, 100, "Finalizing…")
        now = dj_timezone.now()
        self.project.status = ProjectStatus.READY
        self.project.analyzed_at = now
        self.project.save(update_fields=["status", "analyzed_at", "updated_at"])
        self.job.status = JobStatus.SUCCEEDED
        self.job.progress_pct = 100
        self.job.finished_at = now
        self.job.metrics = {**self.job.metrics, **self.metrics}
        self.job.save(
            update_fields=["status", "progress_pct", "finished_at", "metrics", "stage"]
        )
        self._event(JobStage.FINALIZE, "Analysis complete.")

    def _fail(self, message: str) -> None:
        self.job.status = JobStatus.FAILED
        self.job.error_message = message[:4000]
        self.job.finished_at = dj_timezone.now()
        self.job.save(update_fields=["status", "error_message", "finished_at"])
        self.project.status = ProjectStatus.FAILED
        self.project.save(update_fields=["status", "updated_at"])
        self._event(self.job.stage, message, level=EventLevel.ERROR)

    def _update_stage(self, stage: str, progress: float, message: str) -> None:
        self.job.stage = stage
        self.job.progress_pct = progress
        self.job.save(update_fields=["stage", "progress_pct"])
        self._event(stage, message)

    def _event(
        self,
        stage: str,
        message: str,
        *,
        level: str = EventLevel.INFO,
        payload: dict | None = None,
    ) -> None:
        JobEvent.objects.create(
            job=self.job,
            stage=stage,
            message=message,
            level=level,
            payload=payload or {},
        )
