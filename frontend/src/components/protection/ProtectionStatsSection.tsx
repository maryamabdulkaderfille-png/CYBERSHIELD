import { Ban, CalendarClock, ShieldCheck, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "@/components/common/EmptyState";
import { StatCard } from "@/components/dashboard/StatCard";
import { formatRelativeDate } from "@/lib/risk";
import * as protectionService from "@/services/protectionService";
import type { ProtectionStats } from "@/types/protection";

/** Purely additive dashboard widget (Phase 9) — a separate section appended
 * after everything else on the Dashboard Home page. Does not touch any
 * existing widget's markup, state, or data source. */
export function ProtectionStatsSection() {
  const [stats, setStats] = useState<ProtectionStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    protectionService
      .getProtectionStats()
      .then(setStats)
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
          <ShieldCheck size={14} />
          Protection Statistics
        </h2>
        <Link to="/dashboard/protection/blocked" className="text-xs font-medium text-brand-cyan hover:underline">
          View Blocked Websites
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          icon={CalendarClock}
          label="Blocked Today"
          value={isLoading ? "—" : String(stats?.blocked_today ?? 0)}
          accent="danger"
        />
        <StatCard
          icon={TrendingUp}
          label="Blocked This Week"
          value={isLoading ? "—" : String(stats?.blocked_this_week ?? 0)}
          accent="cyan"
        />
        <StatCard
          icon={Ban}
          label="Total Blocked Domains"
          value={isLoading ? "—" : String(stats?.total_blocked_domains ?? 0)}
          accent="blue"
        />
      </div>

      <div className="glass-card p-6">
        <h3 className="mb-4 text-base font-semibold text-slate-100">Recently Blocked Websites</h3>
        {isLoading ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : !stats || stats.recent_blocked.length === 0 ? (
          <EmptyState icon={Ban} title="Nothing blocked yet" description="Blocked websites will show up here." />
        ) : (
          <ul className="divide-y divide-white/5">
            {stats.recent_blocked.map((entry) => (
              <li key={entry.id} className="flex items-center justify-between gap-4 py-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-slate-200">{entry.domain}</p>
                  <p className="text-xs text-slate-500">{formatRelativeDate(entry.blocked_at)}</p>
                </div>
                <span className="shrink-0 text-xs font-semibold text-danger">{entry.trust_score}/100</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
