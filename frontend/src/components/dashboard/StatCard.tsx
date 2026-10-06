import { motion } from "framer-motion";
import { TrendingDown, TrendingUp, type LucideIcon } from "lucide-react";

import { TrendSparkline } from "@/components/dashboard/TrendSparkline";

interface StatCardTrend {
  /** Percentage change vs. the previous 7-day period. Null when there's no prior-period data to compare against. */
  deltaPct: number | null;
  /** True when an upward delta is good news for this metric (e.g. Safe Results) — false when down is good (e.g. Threats Detected). */
  upIsGood: boolean;
  /** Small daily series feeding the sparkline, oldest first. */
  sparkline: (number | null)[];
  /** Marks trend data that isn't backed by a real endpoint yet. */
  isPlaceholder?: boolean;
}

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string;
  accent: "blue" | "danger" | "safe" | "cyan";
  trend?: StatCardTrend;
}

const ACCENT_CLASSES: Record<StatCardProps["accent"], string> = {
  blue: "bg-brand-blue/10 text-brand-blue",
  cyan: "bg-brand-cyan/10 text-brand-cyan",
  safe: "bg-safe/10 text-safe",
  danger: "bg-danger/10 text-danger",
};

export function StatCard({ icon: Icon, label, value, accent, trend }: StatCardProps) {
  const isPositive = trend && trend.deltaPct != null ? (trend.deltaPct >= 0) === trend.upIsGood : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -3 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="glass-card flex items-center gap-4 p-5"
    >
      <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${ACCENT_CLASSES[accent]}`}>
        <Icon size={20} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-2xl font-bold text-slate-50">{value}</p>
        <p className="text-sm text-slate-500">{label}</p>
        {trend && (
          <div className="mt-2 flex items-center justify-between gap-2">
            {trend.deltaPct != null ? (
              <span
                className={`flex items-center gap-0.5 text-xs font-medium ${
                  isPositive ? "text-safe" : "text-danger"
                }`}
                title={trend.isPlaceholder ? "Placeholder — awaiting real period-over-period data." : "vs. previous 7 days"}
              >
                {trend.deltaPct >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                {trend.deltaPct >= 0 ? "+" : ""}
                {trend.deltaPct}% vs last week
                {trend.isPlaceholder && <span className="text-slate-600">*</span>}
              </span>
            ) : (
              <span className="text-xs text-slate-600">—</span>
            )}
            <TrendSparkline
              values={trend.sparkline}
              colorClassName={isPositive === false ? "text-danger" : "text-safe"}
            />
          </div>
        )}
      </div>
    </motion.div>
  );
}
