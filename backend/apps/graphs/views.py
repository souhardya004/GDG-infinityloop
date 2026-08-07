"""Graph query API views."""

from __future__ import annotations

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.graphs.services.neo4j_client import Neo4jGraphStore
from apps.graphs.services.snapshots import ensure_project_graphs, get_snapshot_graph
from apps.parsers.registry import ParserRegistry
from apps.projects.models import Project
from apps.projects.views import get_project_for_user


class GraphView(APIView):
    def get(self, request, project_id, graph_type):
        project = get_project_for_user(project_id, request.user)
        if not project.files.exists() and project.status == "draft":
            return Response(
                {"detail": "Project has no analyzed data yet."},
                status=status.HTTP_409_CONFLICT,
            )

        limit = min(int(request.query_params.get("limit", 800)), 5000)

        # 1) Postgres snapshots (primary — works without Neo4j)
        data = get_snapshot_graph(project, graph_type)
        if not data or not data.get("nodes"):
            data = ensure_project_graphs(project, graph_type)

        # 2) Optional Neo4j enrichment if snapshot empty
        if (
            settings.NEO4J_ENABLED
            and (not data or not data.get("nodes"))
            and graph_type not in {"folder"}
        ):
            try:
                store = Neo4jGraphStore()
                try:
                    neo = store.query_graph(str(project.id), limit=limit)
                    if neo.get("nodes"):
                        data = neo
                finally:
                    store.close()
            except Exception:  # noqa: BLE001
                pass

        if data is None:
            data = {
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

        # Apply client limit
        nodes = (data.get("nodes") or [])[:limit]
        node_uids = {n["uid"] for n in nodes}
        edges = [
            e
            for e in (data.get("edges") or [])
            if e.get("source") in node_uids and e.get("target") in node_uids
        ]
        meta = dict(data.get("meta") or {})
        meta.update(
            {
                "returned_nodes": len(nodes),
                "returned_edges": len(edges),
                "total_nodes": meta.get("total_nodes", len(data.get("nodes") or [])),
                "total_edges": meta.get("total_edges", len(data.get("edges") or [])),
                "truncated": len(data.get("nodes") or []) > limit,
            }
        )

        return Response(
            {
                "project_id": str(project.id),
                "graph_type": graph_type,
                "nodes": nodes,
                "edges": edges,
                "meta": meta,
            }
        )


class NodeDetailView(APIView):
    def get(self, request, project_id, node_uid):
        project = get_project_for_user(project_id, request.user)
        # Search snapshots first
        for snap in project.graphs.all():
            for node in snap.payload.get("nodes") or []:
                if node.get("uid") == node_uid:
                    props = node.get("properties") or {}
                    return Response(
                        {
                            "uid": node_uid,
                            "labels": [node.get("kind") or "Node"],
                            "kind": node.get("kind") or "Node",
                            "properties": props,
                            "documentation": props.get("docstring"),
                            "file_path": props.get("file_path") or props.get("path"),
                            "line_start": props.get("line_start"),
                            "line_end": props.get("line_end"),
                        }
                    )
        if settings.NEO4J_ENABLED:
            try:
                store = Neo4jGraphStore()
                try:
                    node = store.get_node(str(project_id), node_uid)
                finally:
                    store.close()
            except Exception:  # noqa: BLE001
                node = None
        else:
            node = None
        if node is None:
            return Response({"detail": "Node not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(node)


class RebuildGraphsView(APIView):
    """Force rebuild graph snapshots from project files on disk."""

    def post(self, request, project_id):
        project = get_project_for_user(project_id, request.user)
        if (not project.files.exists() or project.status in {"ingesting", "analyzing", "draft"}) and project.sources.exists():
            from apps.analysis.models import AnalysisJob, JobStatus, JobType
            from apps.analysis.pipeline import AnalysisPipeline

            job = AnalysisJob.objects.create(
                project=project,
                job_type=JobType.FULL,
                status=JobStatus.QUEUED,
            )
            AnalysisPipeline(job_id=str(job.id)).run()
            project.refresh_from_db()

        from apps.graphs.services.snapshots import rebuild_fragment_from_disk, save_snapshots

        fragment = rebuild_fragment_from_disk(project)
        counts = save_snapshots(project, fragment)
        return Response(
            {
                "project_id": str(project.id),
                "node_total": len(fragment.get("nodes") or []),
                "edge_total": len(fragment.get("edges") or []),
                "graphs": counts,
            }
        )


class PluginListView(APIView):
    def get(self, request):
        return Response({"plugins": ParserRegistry.default().manifests()})
