"""Postgres-backed graph builders used when Neo4j is unavailable."""

from __future__ import annotations

from typing import Any

from apps.projects.models import Project, ProjectFile


def build_folder_graph(project: Project, *, limit: int = 500) -> dict[str, Any]:
    files = list(project.files.all()[:limit])
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    for pf in files:
        parts = pf.relative_path.split("/")
        file_uid = f"file:{pf.relative_path}"
        nodes[file_uid] = {
            "uid": file_uid,
            "label": parts[-1],
            "kind": "File",
            "properties": {
                "path": pf.relative_path,
                "language": pf.language,
                "loc": pf.line_count,
            },
        }
        parent_uid = None
        for i in range(len(parts) - 1):
            folder_path = "/".join(parts[: i + 1])
            folder_uid = f"folder:{folder_path}"
            nodes[folder_uid] = {
                "uid": folder_uid,
                "label": parts[i],
                "kind": "Folder",
                "properties": {"path": folder_path},
            }
            if parent_uid:
                edges.append(
                    {
                        "id": f"{parent_uid}->{folder_uid}",
                        "source": parent_uid,
                        "target": folder_uid,
                        "type": "CONTAINS",
                        "properties": {},
                    }
                )
            parent_uid = folder_uid
        if parent_uid:
            edges.append(
                {
                    "id": f"{parent_uid}->{file_uid}",
                    "source": parent_uid,
                    "target": file_uid,
                    "type": "CONTAINS",
                    "properties": {},
                }
            )

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "meta": {
            "truncated": project.files.count() > limit,
            "total_nodes": len(nodes),
            "returned_nodes": len(nodes),
            "total_edges": len(edges),
            "returned_edges": len(edges),
            "clusters": [],
        },
    }


def build_file_dependency_graph(project: Project, *, limit: int = 500) -> dict[str, Any]:
    """Best-effort IMPORTS edges are only in Neo4j; here we return file nodes."""
    files = list(ProjectFile.objects.filter(project=project).exclude(language="")[:limit])
    nodes = [
        {
            "uid": f"file:{pf.relative_path}",
            "label": pf.relative_path.split("/")[-1],
            "kind": "File",
            "properties": {
                "path": pf.relative_path,
                "language": pf.language,
                "loc": pf.line_count,
            },
        }
        for pf in files
    ]
    return {
        "nodes": nodes,
        "edges": [],
        "meta": {
            "truncated": False,
            "total_nodes": len(nodes),
            "returned_nodes": len(nodes),
            "total_edges": 0,
            "returned_edges": 0,
            "clusters": [],
            "note": "Import edges require Neo4j. Start Neo4j for full dependency graphs.",
        },
    }
