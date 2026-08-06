import { motion } from "framer-motion";
import { ArrowRight, Network, Upload } from "lucide-react";
import { Link } from "react-router-dom";

export function HomePage() {
  return (
    <section className="relative mx-auto grid min-h-[calc(100vh-5rem)] max-w-7xl items-center gap-10 px-6 py-16 lg:grid-cols-2">
      <div className="space-y-8">
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="font-display text-5xl leading-tight text-white md:text-6xl"
        >
          CodeScope
        </motion.p>
        <motion.h1
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="max-w-xl text-2xl font-medium text-white/85 md:text-3xl"
        >
          Upload a project. See how everything connects.
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="max-w-lg text-base text-white/60"
        >
          Parse source into an architecture graph — dependencies, call flows, classes, and modules —
          then explore it interactively.
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="flex flex-wrap gap-3"
        >
          <Link
            to="/projects/new"
            className="inline-flex items-center gap-2 rounded-full bg-accent px-5 py-3 font-semibold text-ink-950 hover:bg-accent-soft"
          >
            <Upload className="h-4 w-4" />
            Analyze a repo
          </Link>
          <Link
            to="/projects"
            className="inline-flex items-center gap-2 rounded-full border border-white/15 px-5 py-3 text-white/80 hover:bg-white/5"
          >
            View projects
            <ArrowRight className="h-4 w-4" />
          </Link>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.12, duration: 0.5 }}
        className="relative hidden min-h-[420px] overflow-hidden rounded-[2rem] border border-white/10 bg-gradient-to-br from-accent/30 via-ink-900 to-sky-900/40 lg:block"
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(255,255,255,0.12),transparent_45%)]" />
        <div className="absolute inset-8 flex flex-col justify-between">
          <div className="flex items-center gap-2 text-sm text-white/70">
            <Network className="h-4 w-4 text-accent-soft" />
            Live architecture canvas
          </div>
          <div className="grid grid-cols-3 gap-3">
            {["Modules", "Calls", "Imports"].map((label, i) => (
              <motion.div
                key={label}
                animate={{ y: [0, -6, 0] }}
                transition={{ repeat: Infinity, duration: 3.2, delay: i * 0.35 }}
                className="rounded-2xl border border-white/10 bg-ink-950/50 p-4"
              >
                <div className="text-xs uppercase tracking-wider text-white/40">{label}</div>
                <div className="mt-2 font-mono text-lg text-accent-soft">{12 + i * 7}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.div>
    </section>
  );
}
