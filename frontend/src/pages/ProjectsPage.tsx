import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import type { ProjectSummary } from "../types/api";

export function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .listProjects()
      .then(setProjects)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      <div className="mb-8 flex items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl">Projects</h1>
          <p className="mt-2 text-white/55">Analyzed repositories and their current status.</p>
        </div>
        <Link
          to="/projects/new"
          className="rounded-full bg-accent px-4 py-2 text-sm font-semibold text-ink-950"
        >
          New project
        </Link>
      </div>

      {loading && <p className="text-white/50">Loading…</p>}
      {error && (
        <p className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-rose-200">
          {error}
        </p>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {projects.map((project) => (
          <Link
            key={project.id}
            to={`/projects/${project.id}`}
            className="panel block p-5 transition hover:border-accent/40"
          >
            <div className="flex items-start justify-between gap-3">
              <h2 className="text-lg font-semibold">{project.name}</h2>
              <StatusPill status={project.status} />
            </div>
            <p className="mt-3 font-mono text-xs text-white/45">{project.slug}</p>
            <div className="mt-6 flex gap-4 text-sm text-white/60">
              <span>{project.file_count} files</span>
              <span>{project.loc_total.toLocaleString()} LOC</span>
            </div>
            <p className="mt-4 text-xs text-accent-soft">Open full architecture graphs →</p>
          </Link>
        ))}
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const color =
    status === "ready"
      ? "bg-emerald-500/20 text-emerald-300"
      : status === "failed"
        ? "bg-rose-500/20 text-rose-300"
        : "bg-amber-500/20 text-amber-200";
  return <span className={`rounded-full px-2.5 py-1 text-xs capitalize ${color}`}>{status}</span>;
}
