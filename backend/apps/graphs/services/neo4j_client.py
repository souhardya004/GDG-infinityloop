"""Neo4j graph persistence and queries."""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


class Neo4jGraphStore:
    def __init__(self) -> None:
        from neo4j import GraphDatabase

        self._driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )

    def close(self) -> None:
        self._driver.close()

    def replace_project_graph(
        self,
        project_id: str,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
    ) -> None:
        by_uid: dict[str, dict[str, Any]] = {}
        for node in nodes:
            existing = by_uid.get(node["uid"])
            if existing is None:
                by_uid[node["uid"]] = node
            else:
                labels = list({*existing.get("labels", []), *node.get("labels", [])})
                props = {**existing.get("properties", {}), **node.get("properties", {})}
                by_uid[node["uid"]] = {
                    "uid": node["uid"],
                    "labels": labels,
                    "properties": props,
                }

        with self._driver.session() as session:
            session.run(
                "MATCH (n:CodeNode {project_id: $project_id}) DETACH DELETE n",
                project_id=project_id,
            )

            payload = []
            for node in by_uid.values():
                props = dict(node.get("properties") or {})
                props["uid"] = node["uid"]
                props["project_id"] = project_id
                labels = node.get("labels") or ["Node"]
                props["labels"] = labels
                props["kind"] = labels[0]
                payload.append(props)

            for i in range(0, len(payload), 500):
                chunk = payload[i : i + 500]
                session.run(
                    """
                    UNWIND $rows AS row
                    MERGE (n:CodeNode {uid: row.uid, project_id: row.project_id})
                    SET n += row
                    RETURN count(n)
                    """,
                    rows=chunk,
                )

            edge_payload = []
            for idx, edge in enumerate(edges):
                edge_payload.append(
                    {
                        "id": f"e{idx}:{edge['source_uid']}->{edge['target_uid']}:{edge['type']}",
                        "type": edge["type"],
                        "source": edge["source_uid"],
                        "target": edge["target_uid"],
                        "properties": {
                            **(edge.get("properties") or {}),
                            "project_id": project_id,
                        },
                    }
                )

            for i in range(0, len(edge_payload), 500):
                chunk = edge_payload[i : i + 500]
                session.run(
                    """
                    UNWIND $rows AS row
                    MATCH (a:CodeNode {uid: row.source, project_id: $project_id})
                    MATCH (b:CodeNode {uid: row.target, project_id: $project_id})
                    MERGE (a)-[r:REL {id: row.id}]->(b)
                    SET r.type = row.type
                    SET r += row.properties
                    RETURN count(r)
                    """,
                    rows=chunk,
                    project_id=project_id,
                )

    def query_graph(
        self,
        project_id: str,
        *,
        edge_types: list[str] | None = None,
        kinds: list[str] | None = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        type_filter = "AND r.type IN $edge_types" if edge_types else ""
        kind_filter = "AND n.kind IN $kinds" if kinds else ""

        cypher = f"""
        MATCH (n:CodeNode {{project_id: $project_id}})
        WHERE true {kind_filter}
        WITH n LIMIT $limit
        OPTIONAL MATCH (n)-[r:REL]->(m:CodeNode {{project_id: $project_id}})
        WHERE true {type_filter}
        RETURN n, collect(DISTINCT {{rel: r, target: m}}) AS outs
        """
        nodes: dict[str, dict] = {}
        edges: list[dict] = []
        with self._driver.session() as session:
            result = session.run(
                cypher,
                project_id=project_id,
                edge_types=edge_types or [],
                kinds=kinds or [],
                limit=limit,
            )
            for record in result:
                n = record["n"]
                uid = n["uid"]
                nodes[uid] = {
                    "uid": uid,
                    "label": n.get("name") or n.get("path") or uid,
                    "kind": n.get("kind") or "Node",
                    "properties": dict(n),
                }
                for out in record["outs"]:
                    rel = out.get("rel")
                    target = out.get("target")
                    if rel is None or target is None:
                        continue
                    tuid = target["uid"]
                    nodes.setdefault(
                        tuid,
                        {
                            "uid": tuid,
                            "label": target.get("name") or target.get("path") or tuid,
                            "kind": target.get("kind") or "Node",
                            "properties": dict(target),
                        },
                    )
                    edges.append(
                        {
                            "id": rel.get("id") or f"{uid}->{tuid}",
                            "source": uid,
                            "target": tuid,
                            "type": rel.get("type") or "REL",
                            "properties": dict(rel),
                        }
                    )
        return {
            "nodes": list(nodes.values()),
            "edges": edges,
            "meta": {
                "truncated": len(nodes) >= limit,
                "total_nodes": len(nodes),
                "returned_nodes": len(nodes),
                "total_edges": len(edges),
                "returned_edges": len(edges),
                "clusters": [],
            },
        }

    def get_node(self, project_id: str, node_uid: str) -> dict[str, Any] | None:
        with self._driver.session() as session:
            record = session.run(
                """
                MATCH (n:CodeNode {project_id: $project_id, uid: $uid})
                RETURN n
                """,
                project_id=project_id,
                uid=node_uid,
            ).single()
            if record is None:
                return None
            n = record["n"]
            return {
                "uid": n["uid"],
                "labels": [n.get("kind") or "Node"],
                "kind": n.get("kind") or "Node",
                "properties": dict(n),
                "documentation": n.get("docstring") or None,
                "file_path": n.get("file_path") or n.get("path"),
                "line_start": n.get("line_start"),
                "line_end": n.get("line_end"),
            }
