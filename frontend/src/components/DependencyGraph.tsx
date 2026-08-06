import {
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  ReactFlowProvider,
  type Edge,
  type Node,
  type NodeProps,
  useEdgesState,
  useNodesState,
  useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { memo, useEffect, useMemo } from "react";
import type { GraphEdge, GraphNode } from "../types/api";

type Props = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedUid: string | null;
  focusPath?: string | null;
  onSelect: (uid: string | null) => void;
};

type ScopeNodeData = {
  label: string;
  kind: string;
  selected: boolean;
  dimmed: boolean;
};

function kindColor(kind: string): string {
  switch (kind) {
    case "Folder":
      return "#0f766e";
    case "File":
      return "#1d4ed8";
    case "Module":
      return "#0369a1";
    case "Function":
      return "#6d28d9";
    case "Method":
      return "#5b21b6";
    case "Class":
      return "#c2410c";
    case "Interface":
      return "#b45309";
    default:
      return "#334155";
  }
}

const ScopeNode = memo(function ScopeNode({ data }: NodeProps) {
  const d = data as ScopeNodeData;
  return (
    <div
      className={`relative min-w-[128px] max-w-[200px] rounded-xl border px-3 py-2 text-left transition ${
        d.selected
          ? "border-accent bg-accent/20 shadow-[0_0_0_1px_rgba(45,212,191,0.45)]"
          : "border-white/15"
      } ${d.dimmed ? "opacity-25" : "opacity-100"}`}
      style={{ background: d.selected ? undefined : kindColor(d.kind) }}
    >
      <Handle type="target" position={Position.Top} className="!h-2 !w-2 !border-0 !bg-white/40" />
      <div className="text-[10px] uppercase tracking-wider text-white/55">{d.kind}</div>
      <div className="truncate text-[12px] font-medium text-white" title={d.label}>
        {d.label}
      </div>
      <Handle type="source" position={Position.Bottom} className="!h-2 !w-2 !border-0 !bg-white/40" />
    </div>
  );
});

const nodeTypes = { scope: ScopeNode };

export function DependencyGraph(props: Props) {
  return (
    <div className="absolute inset-0">
      <ReactFlowProvider>
        <GraphCanvas {...props} />
      </ReactFlowProvider>
    </div>
  );
}

function GraphCanvas({ nodes, edges, selectedUid, focusPath, onSelect }: Props) {
  const layouted = useMemo(
    () => layoutNodes(nodes, edges, selectedUid, focusPath),
    [nodes, edges, selectedUid, focusPath],
  );
  const [rfNodes, setNodes, onNodesChange] = useNodesState(layouted.nodes);
  const [rfEdges, setEdges, onEdgesChange] = useEdgesState(layouted.edges);

  useEffect(() => {
    setNodes(layouted.nodes);
    setEdges(layouted.edges);
  }, [layouted, setNodes, setEdges]);

  return (
    <ReactFlow
      nodes={rfNodes}
      edges={rfEdges}
      nodeTypes={nodeTypes}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      fitView
      fitViewOptions={{ padding: 0.18, maxZoom: 1.15 }}
      minZoom={0.08}
      maxZoom={2}
      onNodeClick={(_, node) => onSelect(String(node.id))}
      onPaneClick={() => onSelect(null)}
      proOptions={{ hideAttribution: true }}
      defaultEdgeOptions={{
        type: "smoothstep",
        markerEnd: { type: MarkerType.ArrowClosed, width: 14, height: 14, color: "#64748b" },
      }}
    >
      <Background gap={22} size={1} color="rgba(255,255,255,0.045)" />
      <MiniMap
        pannable
        zoomable
        maskColor="rgba(11,18,32,0.78)"
        nodeColor={(n) => kindColor(String((n.data as ScopeNodeData)?.kind || "Node"))}
        className="!bg-ink-950/90 !border !border-white/10"
      />
      <Controls showInteractive={false} className="!bg-ink-950/90 !border !border-white/10 !shadow-none" />
      <FitOnChange fingerprint={layouted.fingerprint} />
    </ReactFlow>
  );
}

function FitOnChange({ fingerprint }: { fingerprint: string }) {
  const { fitView } = useReactFlow();
  useEffect(() => {
    const t = window.setTimeout(() => {
      fitView({ padding: 0.18, duration: 280, maxZoom: 1.15 });
    }, 40);
    return () => window.clearTimeout(t);
  }, [fingerprint, fitView]);
  return null;
}

function layoutNodes(
  nodes: GraphNode[],
  edges: GraphEdge[],
  selectedUid: string | null,
  focusPath?: string | null,
): { nodes: Node[]; edges: Edge[]; fingerprint: string } {
  const layers: Record<string, number> = {
    Folder: 0,
    Module: 1,
    File: 2,
    Class: 3,
    Interface: 3,
    Function: 4,
    Method: 5,
    Node: 3,
  };

  const neighborIds = new Set<string>();
  if (selectedUid) {
    neighborIds.add(selectedUid);
    for (const e of edges) {
      if (e.source === selectedUid) neighborIds.add(e.target);
      if (e.target === selectedUid) neighborIds.add(e.source);
    }
  }

  const focusNorm = focusPath?.replace(/\\/g, "/").toLowerCase() ?? "";
  const focusMatch = (n: GraphNode) => {
    if (!focusNorm) return false;
    const path = String(n.properties.path || n.properties.file_path || "").replace(/\\/g, "/").toLowerCase();
    const label = n.label.toLowerCase();
    return path === focusNorm || path.endsWith("/" + focusNorm) || label === focusNorm.split("/").pop();
  };

  const buckets = new Map<number, GraphNode[]>();
  for (const node of nodes) {
    const layer = layers[node.kind] ?? 3;
    const list = buckets.get(layer) ?? [];
    list.push(node);
    buckets.set(layer, list);
  }

  const rfNodes: Node[] = [];
  const sortedLayers = [...buckets.keys()].sort((a, b) => a - b);
  const layerWidths: number[] = [];

  for (const layer of sortedLayers) {
    const list = buckets.get(layer) ?? [];
    list.sort((a, b) => a.label.localeCompare(b.label));
    const cols = Math.max(1, Math.ceil(Math.sqrt(list.length * 1.35)));
    layerWidths.push(cols);
    list.forEach((node, index) => {
      const col = index % cols;
      const row = Math.floor(index / cols);
      const isFocus = focusMatch(node);
      const selected = node.uid === selectedUid || isFocus;
      const dimmed = Boolean(selectedUid) && !neighborIds.has(node.uid) && !isFocus;
      rfNodes.push({
        id: node.uid,
        type: "scope",
        position: { x: col * 210 + layer * 28, y: layer * 150 + row * 96 },
        data: {
          label: node.label,
          kind: node.kind,
          selected,
          dimmed,
        } satisfies ScopeNodeData,
        selected,
      });
    });
  }

  // Center each layer horizontally relative to the widest layer
  const maxCols = Math.max(1, ...layerWidths);
  let offset = 0;
  for (const layer of sortedLayers) {
    const list = buckets.get(layer) ?? [];
    const cols = Math.max(1, Math.ceil(Math.sqrt(list.length * 1.35)));
    const shift = ((maxCols - cols) * 210) / 2;
    for (let i = 0; i < list.length; i++) {
      const node = rfNodes[offset + i];
      if (node) node.position.x += shift;
    }
    offset += list.length;
  }

  const rfEdges: Edge[] = edges.map((edge) => {
    const active =
      !selectedUid || edge.source === selectedUid || edge.target === selectedUid;
    return {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.type,
      animated: edge.type === "CALLS" || active,
      style: {
        stroke: edgeColor(edge.type),
        strokeWidth: active ? 1.8 : 1,
        opacity: selectedUid && !active ? 0.15 : 0.9,
      },
      labelStyle: { fill: "rgba(226,232,240,0.55)", fontSize: 9 },
      labelBgStyle: { fill: "rgba(11,18,32,0.75)" },
      labelBgPadding: [4, 2] as [number, number],
    };
  });

  return {
    nodes: rfNodes,
    edges: rfEdges,
    fingerprint: `${nodes.length}:${edges.length}:${selectedUid ?? ""}:${focusPath ?? ""}`,
  };
}

function edgeColor(type: string): string {
  switch (type) {
    case "CALLS":
      return "#a78bfa";
    case "IMPORTS":
      return "#38bdf8";
    case "INHERITS":
      return "#fb923c";
    case "CONTAINS":
      return "#2dd4bf";
    case "DECLARES":
      return "#94a3b8";
    default:
      return "#64748b";
  }
}
