import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, GitBranch, Loader2, Plus, Trash2 } from "lucide-react";
import { api } from "../lib/api";
import type { ProjectSummary } from "../types/api";

export function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Deletion modal state
  const [projectToDelete, setProjectToDelete] = useState<ProjectSummary | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    api
      .listProjects()
      .then(setProjects)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async () => {
    if (!projectToDelete) return;
    setDeleting(true);
    try {
      await api.deleteProject(projectToDelete.id);
      setProjects((prev) => prev.filter((p) => p.id !== projectToDelete.id));
      setProjectToDelete(null);
    } catch (err: any) {
      setError(err?.message || "Failed to delete project");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      <div className="mb-8 flex items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-white font-bold tracking-tight">My Projects</h1>
          <p className="mt-1.5 text-sm text-white/55">
            Your private analyzed codebases and interactive architecture graphs.
          </p>
        </div>
        <Link
          to="/projects/new"
          className="inline-flex items-center gap-2 rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-ink-950 transition hover:bg-accent-soft active:scale-[0.99]"
        >
          <Plus className="h-4 w-4" />
          New project
        </Link>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20 text-white/50">
          <Loader2 className="h-6 w-6 animate-spin mr-2 text-accent" />
          <span>Loading your workspaces...</span>
        </div>
      )}

      {error && (
        <div className="mb-6 rounded-2xl border border-rose-500/30 bg-rose-500/10 px-5 py-3 text-sm text-rose-200">
          {error}
        </div>
      )}

      {!loading && projects.length === 0 && (
        <div className="rounded-3xl border border-white/10 bg-white/[0.02] p-12 text-center backdrop-blur-xl">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10 text-accent-soft ring-1 ring-accent/20 mb-4">
            <GitBranch className="h-6 w-6" />
          </div>
          <h3 className="font-display text-lg font-semibold text-white">No projects yet</h3>
          <p className="mx-auto mt-2 max-w-md text-xs text-white/55">
            Upload a ZIP archive or import a GitHub repository to generate an interactive codebase architecture map.
          </p>
          <Link
            to="/projects/new"
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-accent px-5 py-2.5 text-xs font-semibold text-ink-950 hover:bg-accent-soft transition"
          >
            <Plus className="h-4 w-4" />
            Analyze your first repository
          </Link>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {projects.map((project) => (
          <div
            key={project.id}
            className="group relative flex flex-col justify-between rounded-2xl border border-white/10 bg-white/[0.03] p-5 transition-all duration-200 hover:border-accent/40 hover:bg-white/[0.05] hover:shadow-xl"
          >
            <div>
              <div className="flex items-start justify-between gap-3">
                <Link
                  to={`/projects/${project.id}`}
                  className="font-display text-lg font-semibold text-white hover:text-accent transition truncate"
                >
                  {project.name}
                </Link>
                <div className="flex items-center gap-2 shrink-0">
                  <StatusPill status={project.status} />
                  <button
                    type="button"
                    title="Delete project"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      setProjectToDelete(project);
                    }}
                    className="rounded-lg p-1.5 text-white/40 opacity-0 group-hover:opacity-100 hover:bg-red-500/20 hover:text-red-400 transition"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
              <p className="mt-2 font-mono text-xs text-white/40 truncate">{project.slug}</p>
            </div>

            <div className="mt-6">
              <div className="flex items-center gap-4 text-xs text-white/60">
                <span>{project.file_count.toLocaleString()} files</span>
                <span>•</span>
                <span>{project.loc_total.toLocaleString()} LOC</span>
              </div>
              <Link
                to={`/projects/${project.id}`}
                className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium text-accent-soft hover:text-accent transition"
              >
                <span>Open architecture canvas</span>
                <span>→</span>
              </Link>
            </div>
          </div>
        ))}
      </div>

      {/* Delete Confirmation Modal */}
      {projectToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-950/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="w-full max-w-md rounded-2xl border border-white/10 bg-ink-900 p-6 shadow-2xl">
            <div className="flex items-center gap-3 text-red-400 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-500/10 ring-1 ring-red-500/20">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-white">Delete Project</h3>
                <p className="text-xs text-white/50">Permanent action</p>
              </div>
            </div>

            <p className="text-sm text-white/70 leading-relaxed mb-6">
              Are you sure you want to delete <span className="font-semibold text-white">{projectToDelete.name}</span>?
              All associated graphs, analysis jobs, and parsed files will be permanently erased.
            </p>

            <div className="flex items-center justify-end gap-3">
              <button
                type="button"
                disabled={deleting}
                onClick={() => setProjectToDelete(null)}
                className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-white hover:bg-white/10 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={deleting}
                onClick={handleDelete}
                className="inline-flex items-center gap-2 rounded-xl bg-red-500 px-4 py-2 text-xs font-semibold text-white hover:bg-red-600 transition active:scale-[0.99] disabled:opacity-50"
              >
                {deleting ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="h-3.5 w-3.5" />
                    Delete Project
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const color =
    status === "ready"
      ? "bg-emerald-500/20 text-emerald-300 ring-1 ring-emerald-500/30"
      : status === "failed"
        ? "bg-rose-500/20 text-rose-300 ring-1 ring-rose-500/30"
        : "bg-amber-500/20 text-amber-200 ring-1 ring-amber-500/30";
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-medium capitalize ${color}`}>
      {status}
    </span>
  );
}
