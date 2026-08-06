"""Rebuild graphs from project source when snapshots are missing."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from apps.graphs.services.builders import slice_graphs
from apps.graphs.services.postgres_fallback import build_folder_graph
from apps.parsers.registry import ParserRegistry
from apps.projects.models import GraphSnapshot, Project, ProjectFile

logger = logging.getLogger(__name__)


def save_snapshots(project: Project, fragment: dict[str, Any]) -> dict[str, int]:
    graphs = slice_graphs(fragment)
    counts: dict[str, int] = {}
    for graph_type, payload in graphs.items():
        nodes = payload.get("nodes") or []
        edges = payload.get("edges") or []
        GraphSnapshot.objects.update_or_create(
            project=project,
            graph_type=graph_type,
            defaults={
                "payload": payload,
                "node_count": len(nodes),
                "edge_count": len(edges),
            },
        )
        counts[graph_type] = len(nodes)
    return counts


def get_snapshot_graph(project: Project, graph_type: str) -> dict[str, Any] | None:
    snap = GraphSnapshot.objects.filter(project=project, graph_type=graph_type).first()
    if snap and snap.payload:
        return snap.payload
    return None


def rebuild_fragment_from_disk(project: Project) -> dict[str, Any]:
    """Re-parse project files from disk into a graph fragment."""
    root = Path(project.root_path) if project.root_path else None
    nodes: list[dict] = []
    edges: list[dict] = []
    registry = ParserRegistry.default()

    files = list(ProjectFile.objects.filter(project=project))
    for pf in files:
        file_uid = f"file:{pf.relative_path}"
        nodes.append(
            {
                "uid": file_uid,
                "labels": ["File"],
                "properties": {
                    "path": pf.relative_path,
                    "language": pf.language,
                    "loc": pf.line_count,
                    "name": pf.relative_path.split("/")[-1],
                    "project_id": str(project.id),
                },
            }
        )
        parts = pf.relative_path.replace("\\", "/").split("/")
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
                        "project_id": str(project.id),
                    },
                }
            )
            child_uid = file_uid if i == len(parts) - 2 else f"folder:{'/'.join(parts[: i + 2])}"
            edges.append(
                {
                    "type": "CONTAINS",
                    "source_uid": folder_uid,
                    "target_uid": child_uid,
                    "properties": {"project_id": str(project.id)},
                }
            )

        if not root or not pf.language:
            continue
        path = root / pf.relative_path
        if not path.exists():
            continue
        plugin = registry.resolve(pf.relative_path, pf.language)
        if plugin is None:
            continue
        try:
            ir = plugin.parse(pf.relative_path, path.read_bytes())
        except Exception as exc:  # noqa: BLE001
            logger.warning("Rebuild parse failed %s: %s", pf.relative_path, exc)
            continue

        for symbol in ir.symbols:
            labels = ["Symbol"]
            if symbol.kind == "function":
                labels.append("Function")
            elif symbol.kind == "class":
                labels.append("Class")
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
                        "file_path": pf.relative_path,
                        "project_id": str(project.id),
                    },
                }
            )
            edges.append(
                {
                    "type": "DECLARES",
                    "source_uid": file_uid,
                    "target_uid": uid,
                    "properties": {"line": symbol.line_start, "project_id": str(project.id)},
                }
            )
            for base in symbol.bases:
                edges.append(
                    {
                        "type": "INHERITS",
                        "source_uid": uid,
                        "target_uid": f"cl:{base}",
                        "properties": {"project_id": str(project.id), "resolved": False},
                    }
                )
                nodes.append(
                    {
                        "uid": f"cl:{base}",
                        "labels": ["Class", "Symbol"],
                        "properties": {
                            "name": base,
                            "kind": "class",
                            "qualified_name": base,
                            "project_id": str(project.id),
                        },
                    }
                )
            for call in symbol.calls:
                edges.append(
                    {
                        "type": "CALLS",
                        "source_uid": uid,
                        "target_uid": f"fn:{call.callee}",
                        "properties": {
                            "line": call.line,
                            "is_await": call.is_await,
                            "project_id": str(project.id),
                        },
                    }
                )
                nodes.append(
                    {
                        "uid": f"fn:{call.callee}",
                        "labels": ["Function", "Symbol"],
                        "properties": {
                            "name": call.callee,
                            "kind": "function",
                            "qualified_name": call.callee,
                            "project_id": str(project.id),
                        },
                    }
                )

        for imp in ir.imports:
            target = f"file:{imp.resolved_path}" if imp.resolved_path else f"mod:{imp.module}"
            edges.append(
                {
                    "type": "IMPORTS",
                    "source_uid": file_uid,
                    "target_uid": target,
                    "properties": {
                        "names": imp.names,
                        "line": imp.line,
                        "project_id": str(project.id),
                    },
                }
            )
            nodes.append(
                {
                    "uid": target,
                    "labels": ["Module"] if target.startswith("mod:") else ["File"],
                    "properties": {
                        "name": imp.module,
                        "project_id": str(project.id),
                    },
                }
            )

    return {"nodes": nodes, "edges": edges}


def ensure_project_graphs(project: Project, graph_type: str) -> dict[str, Any]:
    """Return a graph payload, rebuilding from disk if snapshots are missing."""
    cached = get_snapshot_graph(project, graph_type)
    if cached and cached.get("nodes"):
        return cached

    # Always can build folder from Postgres files
    if graph_type == "folder" and project.files.exists():
        data = build_folder_graph(project, limit=800)
        GraphSnapshot.objects.update_or_create(
            project=project,
            graph_type="folder",
            defaults={
                "payload": data,
                "node_count": len(data["nodes"]),
                "edge_count": len(data["edges"]),
            },
        )
        if graph_type == "folder":
            return data

    fragment = rebuild_fragment_from_disk(project)
    if not fragment["nodes"]:
        if graph_type == "folder":
            return build_folder_graph(project, limit=800)
        return {
            "nodes": [],
            "edges": [],
            "meta": {
                "truncated": False,
                "total_nodes": 0,
                "returned_nodes": 0,
                "total_edges": 0,
                "returned_edges": 0,
                "clusters": [],
            },
        }

    counts = save_snapshots(project, fragment)
    logger.info("Rebuilt graphs for %s: %s", project.id, counts)
    cached = get_snapshot_graph(project, graph_type)
    return cached or {
        "nodes": [],
        "edges": [],
        "meta": {
            "truncated": False,
            "total_nodes": 0,
            "returned_nodes": 0,
            "total_edges": 0,
            "returned_edges": 0,
            "clusters": [],
        },
    }
