from django.urls import path

from apps.graphs.views import GraphView, NodeDetailView, PluginListView, RebuildGraphsView

urlpatterns = [
    path(
        "projects/<uuid:project_id>/graphs/rebuild/",
        RebuildGraphsView.as_view(),
        name="graphs-rebuild",
    ),
    path(
        "projects/<uuid:project_id>/graphs/<str:graph_type>/",
        GraphView.as_view(),
        name="graph",
    ),
    path(
        "projects/<uuid:project_id>/nodes/<path:node_uid>/",
        NodeDetailView.as_view(),
        name="node-detail",
    ),
    path("plugins/", PluginListView.as_view(), name="plugins"),
]
