import { Link, Outlet } from "react-router-dom";
import { GitBranch, Hexagon } from "lucide-react";

export function AppShell() {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-white/10 bg-ink-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/20 text-accent-soft">
              <Hexagon className="h-5 w-5" />
            </span>
            <div>
              <div className="font-display text-xl font-semibold tracking-tight">CodeScope</div>
              <div className="text-xs text-white/50">Architecture-aware code graphs</div>
            </div>
          </Link>
          <nav className="flex items-center gap-6 text-sm text-white/70">
            <Link className="hover:text-white" to="/projects">
              Projects
            </Link>
            <Link
              className="inline-flex items-center gap-2 rounded-full bg-accent px-4 py-2 font-medium text-ink-950 hover:bg-accent-soft"
              to="/projects/new"
            >
              <GitBranch className="h-4 w-4" />
              New analysis
            </Link>
          </nav>
        </div>
      </header>
      <main className="min-h-[calc(100vh-4.5rem)]">
        <Outlet />
      </main>
    </div>
  );
}
