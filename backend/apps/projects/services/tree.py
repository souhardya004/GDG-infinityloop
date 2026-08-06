"""Build nested file-tree JSON from ProjectFile rows."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from apps.projects.models import ProjectFile


def build_file_tree(project_id) -> list[dict[str, Any]]:
    files = ProjectFile.objects.filter(project_id=project_id).order_by("relative_path")
    root: dict[str, Any] = {"children": {}}

    for pf in files:
        parts = pf.relative_path.replace("\\", "/").split("/")
        node = root
        for i, part in enumerate(parts):
            is_last = i == len(parts) - 1
            children = node.setdefault("children", {})
            if part not in children:
                path = "/".join(parts[: i + 1])
                if is_last:
                    children[part] = {
                        "name": part,
                        "path": path,
                        "type": "file",
                        "language": pf.language,
                        "size_bytes": pf.size_bytes,
                        "line_count": pf.line_count,
                    }
                else:
                    children[part] = {
                        "name": part,
                        "path": path,
                        "type": "folder",
                        "children": {},
                        "file_count": 0,
                        "size_bytes": 0,
                    }
            if not is_last:
                node = children[part]

    def finalize(folder: dict[str, Any]) -> dict[str, Any]:
        kids = folder.get("children") or {}
        out_children: list[dict[str, Any]] = []
        file_count = 0
        size_bytes = 0
        for child in kids.values():
            if child["type"] == "folder":
                finalized = finalize(child)
                file_count += finalized["file_count"]
                size_bytes += finalized["size_bytes"]
                out_children.append(finalized)
            else:
                file_count += 1
                size_bytes += child.get("size_bytes", 0)
                out_children.append(child)
        out_children.sort(key=lambda c: (c["type"] != "folder", c["name"].lower()))
        return {
            "name": folder["name"],
            "path": folder["path"],
            "type": "folder",
            "file_count": file_count,
            "size_bytes": size_bytes,
            "children": out_children,
        }

    result: list[dict[str, Any]] = []
    for child in (root.get("children") or {}).values():
        if child["type"] == "folder":
            result.append(finalize(child))
        else:
            result.append(child)
    result.sort(key=lambda c: (c["type"] != "folder", c["name"].lower()))
    return result
