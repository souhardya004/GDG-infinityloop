import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";

export function NewProjectPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [mode, setMode] = useState<"zip" | "github">("zip");
  const [file, setFile] = useState<File | null>(null);
  const [githubUrl, setGithubUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const project = await api.createProject({ name, description });
      if (mode === "zip") {
        if (!file) throw new Error("Choose a ZIP file.");
        await api.ingestZip(project.id, file);
      } else {
        await api.ingestGitHub(project.id, { url: githubUrl, branch });
      }
      navigate(`/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start analysis");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-10">
      <h1 className="font-display text-3xl">New analysis</h1>
      <p className="mt-2 text-white/55">Upload a ZIP or clone a GitHub repository.</p>

      <form onSubmit={onSubmit} className="panel mt-8 space-y-5 p-6">
        <label className="block space-y-2 text-sm">
          <span className="text-white/70">Project name</span>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-ink-950 px-3 py-2 outline-none focus:border-accent"
            placeholder="payments-api"
          />
        </label>

        <label className="block space-y-2 text-sm">
          <span className="text-white/70">Description</span>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="min-h-24 w-full rounded-xl border border-white/10 bg-ink-950 px-3 py-2 outline-none focus:border-accent"
            placeholder="Optional notes"
          />
        </label>

        <div className="flex gap-2 rounded-full bg-ink-950 p-1">
          {(["zip", "github"] as const).map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => setMode(value)}
              className={`flex-1 rounded-full px-3 py-2 text-sm capitalize ${
                mode === value ? "bg-accent text-ink-950" : "text-white/60"
              }`}
            >
              {value === "zip" ? "ZIP upload" : "GitHub"}
            </button>
          ))}
        </div>

        {mode === "zip" ? (
          <label className="block space-y-2 text-sm">
            <span className="text-white/70">ZIP archive</span>
            <input
              type="file"
              accept=".zip"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="w-full text-white/70 file:mr-3 file:rounded-full file:border-0 file:bg-white/10 file:px-3 file:py-1.5"
            />
          </label>
        ) : (
          <div className="space-y-4">
            <label className="block space-y-2 text-sm">
              <span className="text-white/70">Repository URL</span>
              <input
                required={mode === "github"}
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-ink-950 px-3 py-2 outline-none focus:border-accent"
                placeholder="https://github.com/org/repo"
              />
            </label>
            <label className="block space-y-2 text-sm">
              <span className="text-white/70">Branch</span>
              <input
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-ink-950 px-3 py-2 outline-none focus:border-accent"
              />
            </label>
          </div>
        )}

        {error && <p className="text-sm text-rose-300">{error}</p>}

        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-full bg-accent py-3 font-semibold text-ink-950 disabled:opacity-60"
        >
          {busy ? "Starting analysis…" : "Start analysis"}
        </button>
      </form>
    </div>
  );
}
