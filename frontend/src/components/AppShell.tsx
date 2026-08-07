import { useState } from "react";
import { Link, Outlet, useNavigate } from "react-router-dom";
import { GitBranch, Hexagon, LogOut, ShieldCheck, User } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export function AppShell() {
  const { user, isAuthenticated, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = async () => {
    setDropdownOpen(false);
    await logout();
    navigate("/login");
  };

  const displayName =
    user?.first_name || user?.username || (user?.email ? user.email.split("@")[0] : "Account");

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-white/10 bg-ink-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3.5">
          <Link to="/" className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/20 text-accent-soft ring-1 ring-accent/30 shadow-md shadow-accent/10">
              <Hexagon className="h-5 w-5" />
            </span>
            <div>
              <div className="font-display text-lg font-bold tracking-tight text-white flex items-center gap-2">
                CodeScope
                <span className="rounded-full bg-accent/10 px-2 py-0.5 text-[10px] font-mono text-accent-soft ring-1 ring-accent/20">
                  Private
                </span>
              </div>
              <div className="text-xs text-white/50">Architecture-aware code intelligence</div>
            </div>
          </Link>

          <nav className="flex items-center gap-4 text-sm text-white/70">
            {isAuthenticated ? (
              <>
                <Link className="hover:text-white transition px-2 py-1" to="/projects">
                  My Projects
                </Link>
                <Link
                  className="inline-flex items-center gap-2 rounded-xl bg-accent px-3.5 py-1.5 text-xs font-semibold text-ink-950 hover:bg-accent-soft transition active:scale-[0.99]"
                  to="/projects/new"
                >
                  <GitBranch className="h-3.5 w-3.5" />
                  New analysis
                </Link>

                {/* User Avatar & Menu */}
                <div className="relative ml-2">
                  <button
                    type="button"
                    onClick={() => setDropdownOpen((prev) => !prev)}
                    className="flex items-center gap-2.5 rounded-xl border border-white/10 bg-white/5 p-1.5 pr-3 text-xs font-medium text-white transition hover:bg-white/10 hover:border-white/20"
                  >
                    {user?.avatar_url ? (
                      <img
                        src={user.avatar_url}
                        alt={displayName}
                        className="h-7 w-7 rounded-lg object-cover ring-1 ring-white/20"
                      />
                    ) : (
                      <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/20 text-accent-soft font-semibold ring-1 ring-accent/30">
                        {displayName.charAt(0).toUpperCase()}
                      </span>
                    )}
                    <span className="max-w-[120px] truncate">{displayName}</span>
                  </button>

                  {/* Dropdown Menu */}
                  {dropdownOpen && (
                    <>
                      <div
                        className="fixed inset-0 z-40"
                        onClick={() => setDropdownOpen(false)}
                      />
                      <div className="absolute right-0 top-full mt-2 w-56 rounded-2xl border border-white/10 bg-ink-950/95 p-2 backdrop-blur-xl shadow-2xl z-50 animate-in fade-in zoom-in-95 duration-100">
                        <div className="px-3 py-2 border-b border-white/10">
                          <div className="text-xs font-semibold text-white truncate">{displayName}</div>
                          <div className="text-[11px] text-white/50 truncate">{user?.email}</div>
                          <div className="mt-1 inline-flex items-center gap-1 text-[10px] text-emerald-400 font-mono">
                            <ShieldCheck className="h-3 w-3" />
                            <span>Private Isolation Active</span>
                          </div>
                        </div>

                        <div className="py-1">
                          <Link
                            to="/projects"
                            onClick={() => setDropdownOpen(false)}
                            className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-white/80 hover:bg-white/10 hover:text-white transition"
                          >
                            <User className="h-3.5 w-3.5 text-white/50" />
                            My Projects
                          </Link>
                          <Link
                            to="/projects/new"
                            onClick={() => setDropdownOpen(false)}
                            className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-white/80 hover:bg-white/10 hover:text-white transition"
                          >
                            <GitBranch className="h-3.5 w-3.5 text-white/50" />
                            New Analysis
                          </Link>
                        </div>

                        <div className="pt-1 border-t border-white/10">
                          <button
                            type="button"
                            onClick={handleLogout}
                            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-red-400 hover:bg-red-500/10 transition"
                          >
                            <LogOut className="h-3.5 w-3.5" />
                            Sign Out
                          </button>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </>
            ) : (
              <div className="flex items-center gap-3">
                <Link
                  className="rounded-xl px-3 py-1.5 text-xs font-medium text-white/80 hover:text-white transition"
                  to="/login"
                >
                  Sign In
                </Link>
                <Link
                  className="rounded-xl bg-accent px-4 py-1.5 text-xs font-semibold text-ink-950 hover:bg-accent-soft transition"
                  to="/login?tab=signup"
                >
                  Get Started
                </Link>
              </div>
            )}
          </nav>
        </div>
      </header>
      <main className="min-h-[calc(100vh-4.5rem)]">
        <Outlet />
      </main>
    </div>
  );
}

