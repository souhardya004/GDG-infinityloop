import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  FolderTree,
  PanelRightClose,
  PanelRightOpen,
  RefreshCw,
  Search,
  X,
} from "lucide-react";
import { DependencyGraph } from "../components/DependencyGraph";
import { FileTree } from "../components/FileTree";
import { api } from "../lib/api";
import type { FileTreeNode, GraphResponse, Project } from "../types/api";

const VIEWS = [
  { type: "architecture", label: "Architecture", hint: "Full project: files, classes, functions" },
  { type: "dependency", label: "Dependencies", hint: "Imports & package links" },
  { type: "call", label: "Call graph", hint: "Function / method call flow" },
  { type: "class", label: "Classes", hint: "Inheritance & interfaces" },
  { type: "module", label: "Modules", hint: "Module / file map" },
  { type: "folder", label: "Folders", hint: "Directory containment (optional)" },
] as const;

const LEGEND = [
  { kind: "File", color: "#1d4ed8" },
  { kind: "Module", color: "#0369a1" },
  { kind: "Class", color: "#c2410c" },
  { kind: "Function", color: "#6d28d9" },
  { kind: "Folder", color: "#0f766e" },
];

export function ProjectDashboardPage() {
  const { projectId = "" } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const graphType = searchParams.get("view") || "architecture";

  const [project, setProject] = useState<Project | null>(null);
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [tree, setTree] = useState<FileTreeNode[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [focusPath, setFocusPath] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [graphLoading, setGraphLoading] = useState(false);
  const [filesOpen, setFilesOpen] = useState(false);
  const [inspectorOpen, setInspectorOpen] = useState(true);
  const autoRebuildTried = useRef(false);

  const loadProject = useCallback(async () => {
    const p = await api.getProject(projectId);
    setProject(p);
    try {
      const t = await api.getFileTree(projectId);
      setTree(t.tree ?? []);
    } catch {
      setTree([]);
    }
    return p;
  }, [projectId]);

  const loadGraph = useCallback(
    async (type: string) => {
      setGraphLoading(true);
      setError(null);
      try {
        const g = await api.getGraph(projectId, type);
        setGraph(g);
        return g;
      } catch (err) {
        setGraph(null);
        setError(err instanceof Error ? err.message : "Failed to load graph");
        return null;
      } finally {
        setGraphLoading(false);
      }
    },
    [projectId],
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await loadProject();
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load");
      }
    })();
    const timer = window.setInterval(() => {
      loadProject().catch(() => undefined);
    }, 5000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [loadProject]);

  useEffect(() => {
    if (!projectId) return;
    autoRebuildTried.current = false;
    loadGraph(graphType);
  }, [projectId, graphType, loadGraph]);

  // Auto-rebuild once when project is ready but this view has zero nodes
  useEffect(() => {
    if (!project || project.status !== "ready") return;
    if (!graph || graph.nodes.length > 0) return;
    if (graphLoading || busy || autoRebuildTried.current) return;
    autoRebuildTried.current = true;
    (async () => {
      setBusy(true);
      try {
        await api.rebuildGraphs(projectId);
        await loadGraph(graphType);
        await loadProject();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Auto-rebuild failed");
      } finally {
        setBusy(false);
      }
    })();
  }, [project, graph, graphLoading, busy, projectId, graphType, loadGraph, loadProject]);

  const selectedNode = useMemo(
    () => graph?.nodes.find((n) => n.uid === selected) ?? null,
    [graph, selected],
  );

  const filteredNodes = useMemo(() => {
    if (!graph) return [];
    const q = query.trim().toLowerCase();
    if (!q) return graph.nodes;
    return graph.nodes.filter(
      (n) =>
        n.label.toLowerCase().includes(q) ||
        n.uid.toLowerCase().includes(q) ||
        n.kind.toLowerCase().includes(q) ||
        String(n.properties.path || n.properties.file_path || "")
          .toLowerCase()
          .includes(q),
    );
  }, [graph, query]);

  const displayGraph = useMemo(() => {
    if (!graph) return null;
    if (!query.trim()) return graph;
    const keep = new Set(filteredNodes.map((n) => n.uid));
    return {
      ...graph,
      nodes: filteredNodes,
      edges: graph.edges.filter((e) => keep.has(e.source) && keep.has(e.target)),
    };
  }, [graph, filteredNodes, query]);

  async function onRebuild() {
    setBusy(true);
    setError(null);
    try {
      await api.rebuildGraphs(projectId);
      await loadGraph(graphType);
      await loadProject();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rebuild failed");
    } finally {
      setBusy(false);
    }
  }

  function onSelectFile(path: string) {
    setFocusPath(path);
    setFilesOpen(false);
    const match =
      graph?.nodes.find((n) => {
        const p = String(n.properties.path || n.properties.file_path || "").replace(/\\/g, "/");
        return p === path || n.label === path.split("/").pop();
      }) ?? null;
    setSelected(match?.uid ?? null);
    if (match) setInspectorOpen(true);
  }

  if (!project && error) {
    return <p className="p-10 text-rose-300">{error}</p>;
  }
  if (!project) {
    return <p className="p-10 text-white/50">Loading project…</p>;
  }

  const analyzing = project.status === "analyzing" || project.status === "ingesting";

  return (
    <div className="relative flex h-[calc(100vh-4.5rem)] flex-col overflow-hidden">
      {/* Compact top bar — graphs live HERE, not inside folders */}
      <header className="z-20 shrink-0 border-b border-white/10 bg-ink-950/95 px-4 py-2.5 backdrop-blur">
        <div className="flex flex-wrap items-center gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 text-[11px] uppercase tracking-wider text-accent-soft">
              <span className={analyzing ? "animate-pulse" : ""}>{project.status}</span>
              <span className="text-white/20">·</span>
              <Link to="/projects" className="text-white/45 hover:text-white">
                Projects
              </Link>
            </div>
            <h1 className="truncate font-display text-xl leading-tight md:text-2xl">{project.name}</h1>
          </div>

          <div className="hidden flex-wrap gap-2 text-xs text-white/60 sm:flex">
            <StatPill label="Files" value={project.stats.file_count} />
            <StatPill label="LOC" value={project.stats.loc_total} />
            <StatPill label="Fns" value={project.stats.function_count} />
            <StatPill label="Classes" value={project.stats.class_count} />
          </div>

          <button
            type="button"
            onClick={() => setFilesOpen((v) => !v)}
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm ${
              filesOpen
                ? "border-accent/40 bg-accent/10 text-accent-soft"
                : "border-white/15 text-white/80 hover:bg-white/5"
            }`}
            title="Browse source files (does not hide the graph)"
          >
            <FolderTree className="h-3.5 w-3.5" />
            Files
          </button>

          <button
            type="button"
            onClick={() => setInspectorOpen((v) => !v)}
            className="inline-flex items-center gap-2 rounded-full border border-white/15 px-3 py-1.5 text-sm text-white/80 hover:bg-white/5"
          >
            {inspectorOpen ? <PanelRightClose className="h-3.5 w-3.5" /> : <PanelRightOpen className="h-3.5 w-3.5" />}
            Details
          </button>

          <button
            type="button"
            onClick={onRebuild}
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-full border border-white/15 px-3 py-1.5 text-sm text-white/80 hover:bg-white/5 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${busy ? "animate-spin" : ""}`} />
            Rebuild
          </button>
        </div>

        <div className="mt-2.5 flex flex-wrap items-center gap-1">
          {VIEWS.map((view) => {
            const active = graphType === view.type;
            return (
              <button
                key={view.type}
                type="button"
                title={view.hint}
                onClick={() => {
                  setSelected(null);
                  setSearchParams({ view: view.type });
                }}
                className={`rounded-full px-3 py-1.5 text-sm transition ${
                  active
                    ? "bg-accent font-semibold text-ink-950"
                    : "text-white/55 hover:bg-white/5 hover:text-white"
                }`}
              >
                {view.label}
              </button>
            );
          })}
          <span className="ml-2 hidden text-xs text-white/35 lg:inline">
            Full graphs on this page — no folder drill-down required
          </span>
        </div>
      </header>

      {/* FULL GRAPH canvas — primary surface */}
      <div className="relative min-h-0 flex-1">
        <div className="absolute left-3 top-3 z-10 flex items-center gap-2 rounded-full border border-white/10 bg-ink-950/85 px-3 py-1.5 backdrop-blur">
          <Search className="h-3.5 w-3.5 text-white/40" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter nodes, paths, kinds…"
            className="w-44 bg-transparent text-sm outline-none placeholder:text-white/30 md:w-64"
          />
          {query && (
            <button type="button" onClick={() => setQuery("")} className="text-white/40 hover:text-white">
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        <div className="absolute bottom-3 left-3 z-10 flex flex-wrap gap-2 rounded-xl border border-white/10 bg-ink-950/85 px-3 py-2 text-[11px] text-white/55 backdrop-blur">
          {LEGEND.map((item) => (
            <span key={item.kind} className="inline-flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm" style={{ background: item.color }} />
              {item.kind}
            </span>
          ))}
        </div>

        {error && (
          <div className="absolute right-3 top-3 z-10 max-w-sm rounded-xl border border-rose-500/30 bg-rose-950/85 px-3 py-2 text-xs text-rose-100">
            {error}
          </div>
        )}

        {graphLoading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-ink-950/35 text-sm text-white/60">
            Loading full graph…
          </div>
        )}

        {analyzing && (
          <div className="absolute inset-x-0 top-14 z-10 mx-auto w-fit rounded-full border border-amber-400/30 bg-amber-950/80 px-4 py-2 text-xs text-amber-100">
            Analysis in progress — graphs will appear here when ready
          </div>
        )}

        {displayGraph && displayGraph.nodes.length === 0 && !graphLoading ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 p-8 text-center">
            <p className="text-lg text-white/75">No graph nodes yet</p>
            <p className="max-w-md text-sm text-white/45">
              {analyzing
                ? "Waiting for analysis to finish…"
                : "Click Rebuild to generate architecture graphs from source on disk."}
            </p>
            {!analyzing && (
              <button
                type="button"
                onClick={onRebuild}
                disabled={busy}
                className="rounded-full bg-accent px-4 py-2 text-sm font-semibold text-ink-950 disabled:opacity-50"
              >
                {busy ? "Rebuilding…" : "Rebuild graphs now"}
              </button>
            )}
          </div>
        ) : (
          displayGraph && (
            <DependencyGraph
              nodes={displayGraph.nodes}
              edges={displayGraph.edges}
              selectedUid={selected}
              focusPath={focusPath}
              onSelect={(uid) => {
                setSelected(uid);
                if (uid) setInspectorOpen(true);
              }}
            />
          )
        )}

        {/* Optional files drawer — overlay, does NOT replace the graph */}
        {filesOpen && (
          <aside className="absolute bottom-0 left-0 top-0 z-20 flex w-[280px] flex-col border-r border-white/10 bg-ink-950/95 shadow-2xl backdrop-blur md:w-[300px]">
            <div className="flex items-center justify-between border-b border-white/10 px-3 py-2">
              <div className="text-xs uppercase tracking-wider text-white/40">Source files</div>
              <button type="button" onClick={() => setFilesOpen(false)} className="text-white/40 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="min-h-0 flex-1 overflow-auto p-2">
              {tree.length === 0 ? (
                <p className="p-2 text-xs text-white/40">
                  {project.stats.file_count > 0
                    ? "Tree unavailable — try Rebuild."
                    : "Waiting for analysis…"}
                </p>
              ) : (
                <FileTree nodes={tree} selectedPath={focusPath} onSelectFile={onSelectFile} />
              )}
            </div>
            <div className="space-y-1 border-t border-white/10 p-3">
              {project.languages.map((lang) => (
                <div key={lang.language} className="rounded-lg bg-white/5 px-2 py-1 text-xs text-white/55">
                  {lang.language} · {lang.file_count} files
                </div>
              ))}
            </div>
          </aside>
        )}

        {/* Inspector — side panel over graph, not a separate route */}
        {inspectorOpen && (
          <aside className="absolute bottom-0 right-0 top-0 z-20 flex w-[280px] flex-col border-l border-white/10 bg-ink-950/95 backdrop-blur md:w-[320px]">
            <div className="flex items-center justify-between border-b border-white/10 px-4 py-2">
              <div className="text-xs uppercase tracking-wider text-white/40">Inspector</div>
              <button type="button" onClick={() => setInspectorOpen(false)} className="text-white/40 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="min-h-0 flex-1 overflow-auto p-4">
              {!selectedNode ? (
                <div className="space-y-3 text-sm text-white/50">
                  <p>
                    Click any node on the full graph to inspect it. Switch views with the tabs above —
                    everything stays on this page.
                  </p>
                  <p className="text-xs text-white/35">
                    Tip: open <span className="text-white/55">Files</span> to jump to a source file on
                    the graph without leaving this canvas.
                  </p>
                </div>
              ) : (
                <div className="space-y-3 text-sm">
                  <div>
                    <div className="text-white/40">Name</div>
                    <div className="text-base font-semibold">{selectedNode.label}</div>
                  </div>
                  <div>
                    <div className="text-white/40">Kind</div>
                    <div className="font-mono text-accent-soft">{selectedNode.kind}</div>
                  </div>
                  <div>
                    <div className="text-white/40">UID</div>
                    <div className="break-all font-mono text-[11px] text-white/55">{selectedNode.uid}</div>
                  </div>
                  <pre className="max-h-[55vh] overflow-auto rounded-xl bg-ink-900 p-3 font-mono text-[11px] text-white/65">
                    {JSON.stringify(selectedNode.properties, null, 2)}
                  </pre>
                </div>
              )}
            </div>
            {graph && (
              <p className="border-t border-white/10 px-4 py-2 text-xs text-white/35">
                {graph.meta.returned_nodes} nodes · {graph.meta.returned_edges} edges
                {graph.meta.truncated ? " (truncated)" : ""}
              </p>
            )}
          </aside>
        )}
      </div>
    </div>
  );
}

function StatPill({ label, value }: { label: string; value: number }) {
  return (
    <span className="rounded-full border border-white/10 bg-ink-900/80 px-2.5 py-1">
      <span className="text-white/35">{label} </span>
      <span className="font-mono text-white">{Number(value).toLocaleString()}</span>
    </span>
  );
}
