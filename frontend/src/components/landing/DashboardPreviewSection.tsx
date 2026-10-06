import { motion } from "framer-motion";
import { AlertTriangle, LayoutDashboard, ShieldCheck, TrendingUp } from "lucide-react";

import { StatCard } from "@/components/dashboard/StatCard";

export function DashboardPreviewSection() {
  return (
    <section id="dashboard-preview" className="mx-auto max-w-7xl px-6 py-20">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="mx-auto max-w-2xl text-center"
      >
        <h2 className="text-3xl font-bold text-slate-50">A dashboard that actually explains itself</h2>
        <p className="mt-3 text-slate-400">
          Illustrative preview — your real dashboard fills in with your own scan history from day one.
        </p>
      </motion.div>

      {/* A "coming into focus" 3D tilt-in reveal — distinct from the plain
          fade-up used elsewhere on the page, fitting for the one section
          that previews an actual product screen. One-time on scroll-in,
          not continuous, since a permanently tilted data panel would hurt
          readability. */}
      <div className="mx-auto mt-12 max-w-5xl" style={{ perspective: 1200 }}>
        <motion.div
          initial={{ opacity: 0, rotateX: 10, scale: 0.95, y: 24 }}
          whileInView={{ opacity: 1, rotateX: 0, scale: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, delay: 0.1, ease: "easeOut" }}
          className="glass-card relative overflow-hidden p-6 sm:p-8"
        >
          <div className="absolute right-4 top-4 flex items-center gap-1.5 rounded-full border border-white/10 bg-navy-950/80 px-3 py-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
            <LayoutDashboard size={12} aria-hidden="true" />
            Preview
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard icon={ShieldCheck} label="Security Score" value="87 / 100" accent="cyan" />
            <StatCard icon={TrendingUp} label="Scans This Week" value="42" accent="blue" />
            <StatCard icon={AlertTriangle} label="Threats Blocked" value="6" accent="danger" />
            <StatCard icon={LayoutDashboard} label="Scan Types Used" value="3 / 3" accent="safe" />
          </div>

          <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
            <div className="glass-panel p-5 lg:col-span-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Weekly Activity</p>
              <div className="mt-4 flex h-24 items-end gap-2">
                {[30, 55, 40, 70, 45, 80, 60].map((height, index) => (
                  <motion.div
                    key={index}
                    initial={{ scaleY: 0 }}
                    whileInView={{ scaleY: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.4, delay: 0.3 + index * 0.05, ease: "easeOut" }}
                    className="flex-1 origin-bottom rounded-t-md bg-gradient-to-t from-brand-blue/40 to-brand-cyan/70"
                    style={{ height: `${height}%` }}
                  />
                ))}
              </div>
            </div>
            <div className="glass-panel p-5">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Risk Distribution</p>
              <div className="mt-4 space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Safe</span>
                  <span>68%</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/5">
                  <motion.div
                    initial={{ scaleX: 0 }}
                    whileInView={{ scaleX: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5, delay: 0.4, ease: "easeOut" }}
                    className="h-1.5 w-[68%] origin-left rounded-full bg-safe"
                  />
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Suspicious</span>
                  <span>21%</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/5">
                  <motion.div
                    initial={{ scaleX: 0 }}
                    whileInView={{ scaleX: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5, delay: 0.5, ease: "easeOut" }}
                    className="h-1.5 w-[21%] origin-left rounded-full bg-warning"
                  />
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Dangerous</span>
                  <span>11%</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/5">
                  <motion.div
                    initial={{ scaleX: 0 }}
                    whileInView={{ scaleX: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5, delay: 0.6, ease: "easeOut" }}
                    className="h-1.5 w-[11%] origin-left rounded-full bg-danger"
                  />
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
