"""Typed graph builders from a raw node/edge fragment (no Neo4j required)."""

from __future__ import annotations

from typing import Any


def _meta(nodes: list, edges: list, truncated: bool = False) -> dict[str, Any]:
    return {
        "truncated": truncated,
        "total_nodes": len(nodes),
        "returned_nodes": len(nodes),
        "total_edges": len(edges),
        "returned_edges": len(edges),
        "clusters": [],
    }


def _to_dto(nodes: list[dict], edges: list[dict], *, limit: int = 800) -> dict[str, Any]:
    # Deduplicate nodes
    by_uid: dict[str, dict] = {}
    for node in nodes:
        uid = node.get("uid")
        if not uid:
            continue
        labels = node.get("labels") or []
        props = dict(node.get("properties") or {})
        kind = props.get("kind") or (labels[-1] if labels else "Node")
        if "Class" in labels:
            kind = "Class"
        elif "Function" in labels:
            kind = "Function"
        elif "Method" in labels:
            kind = "Method"
        elif "Folder" in labels:
            kind = "Folder"
        elif "File" in labels:
            kind = "File"
        elif "Module" in labels:
            kind = "Module"
        label = (
            props.get("name")
            or props.get("path")
            or uid.split(":")[-1]
        )
        existing = by_uid.get(uid)
        if existing is None:
            by_uid[uid] = {
                "uid": uid,
                "label": str(label).split("/")[-1],
                "kind": kind,
                "properties": props,
            }
        else:
            existing["properties"].update(props)

    truncated = len(by_uid) > limit
    kept = list(by_uid.values())[:limit]
    kept_uids = {n["uid"] for n in kept}

    edge_dtos = []
    for idx, edge in enumerate(edges):
        src = edge.get("source_uid") or edge.get("source")
        tgt = edge.get("target_uid") or edge.get("target")
        if src not in kept_uids or tgt not in kept_uids:
            continue
        edge_dtos.append(
            {
                "id": edge.get("id") or f"e{idx}:{src}->{tgt}:{edge.get('type')}",
                "source": src,
                "target": tgt,
                "type": edge.get("type") or "REL",
                "properties": edge.get("properties") or {},
            }
        )

    return {"nodes": kept, "edges": edge_dtos, "meta": _meta(kept, edge_dtos, truncated)}


def slice_graphs(fragment: dict[str, Any], *, limit: int = 800) -> dict[str, dict[str, Any]]:
    """Build all visualization graphs from one analysis fragment."""
    nodes = fragment.get("nodes") or []
    edges = fragment.get("edges") or []

    def filter_nodes(predicate):
        return [n for n in nodes if predicate(n)]

    def filter_edges(types: set[str], allowed_uids: set[str] | None = None):
        out = []
        for e in edges:
            if e.get("type") not in types:
                continue
            src = e.get("source_uid")
            tgt = e.get("target_uid")
            if allowed_uids is not None and (src not in allowed_uids or tgt not in allowed_uids):
                # still keep edge if endpoints exist in full set — add missing as stubs later
                pass
            out.append(e)
        return out

    folder_nodes = filter_nodes(lambda n: "Folder" in (n.get("labels") or []) or "File" in (n.get("labels") or []))
    folder_edges = filter_edges({"CONTAINS"})
    folder_uids = {n["uid"] for n in folder_nodes}
    # Include endpoints referenced by CONTAINS
    for e in folder_edges:
        folder_uids.add(e["source_uid"])
        folder_uids.add(e["target_uid"])
    folder_nodes = [n for n in nodes if n["uid"] in folder_uids] or folder_nodes

    import_edges = filter_edges({"IMPORTS", "DEPENDS_ON"})
    import_uids = set()
    for e in import_edges:
        import_uids.add(e["source_uid"])
        import_uids.add(e["target_uid"])
    dep_nodes = [n for n in nodes if n["uid"] in import_uids]
    if not dep_nodes:
        dep_nodes = filter_nodes(lambda n: "File" in (n.get("labels") or []) or "Module" in (n.get("labels") or []))

    call_edges = filter_edges({"CALLS"})
    call_uids = set()
    for e in call_edges:
        call_uids.add(e["source_uid"])
        call_uids.add(e["target_uid"])
    call_nodes = [n for n in nodes if n["uid"] in call_uids]
    # Ensure unresolved call targets still appear
    existing = {n["uid"] for n in call_nodes}
    for uid in call_uids:
        if uid in existing:
            continue
        name = uid.split(":", 1)[-1]
        call_nodes.append(
            {
                "uid": uid,
                "labels": ["Function", "Symbol"],
                "properties": {"name": name, "kind": "function", "qualified_name": name},
            }
        )

    class_edges = filter_edges({"INHERITS", "IMPLEMENTS", "DECLARES", "COMPOSES"})
    class_nodes = [
        n
        for n in nodes
        if "Class" in (n.get("labels") or [])
        or "Interface" in (n.get("labels") or [])
        or "Method" in (n.get("labels") or [])
    ]
    # Prefer class + inheritance focus for class diagram
    class_focus = [
        n for n in nodes if "Class" in (n.get("labels") or []) or "Interface" in (n.get("labels") or [])
    ]
    if class_focus:
        class_nodes = class_focus
        class_edges = filter_edges({"INHERITS", "IMPLEMENTS"})

    module_nodes = filter_nodes(
        lambda n: "Module" in (n.get("labels") or []) or "File" in (n.get("labels") or [])
    )
    module_edges = filter_edges({"IMPORTS", "DEPENDS_ON"})

    # Architecture: files + imports + key symbols (overview)
    arch_nodes = filter_nodes(
        lambda n: "File" in (n.get("labels") or [])
        or "Class" in (n.get("labels") or [])
        or "Function" in (n.get("labels") or [])
    )
    arch_edges = filter_edges({"IMPORTS", "DECLARES", "CALLS", "INHERITS"})

    return {
        "folder": _to_dto(folder_nodes, folder_edges, limit=limit),
        "file_dependency": _to_dto(dep_nodes, import_edges, limit=limit),
        "dependency": _to_dto(dep_nodes, import_edges, limit=limit),
        "call": _to_dto(call_nodes, call_edges, limit=limit),
        "class": _to_dto(class_nodes, class_edges, limit=limit),
        "module": _to_dto(module_nodes, module_edges, limit=limit),
        "architecture": _to_dto(arch_nodes, arch_edges, limit=limit),
    }
