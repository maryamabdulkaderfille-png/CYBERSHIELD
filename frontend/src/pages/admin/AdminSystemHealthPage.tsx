import { Activity, Clock, Database, Gauge, HardDrive } from "lucide-react";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/common/EmptyState";
import { extractErrorMessage } from "@/lib/errors";
import * as adminService from "@/services/adminService";
import type { SystemHealth } from "@/types/admin";

function formatUptime(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export function AdminSystemHealthPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    adminService
      .getSystemHealth()
      .then(setHealth)
      .catch((err) => setError(extractErrorMessage(err, "Could not load system health.")))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <p className="text-sm text-slate-500">Loading…</p>;
  if (error || !health) {
    return <div className="glass-card border-danger/20 p-4 text-sm text-danger">{error}</div>;
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold text-slate-50">
          <Activity size={22} />
          System Monitoring
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Live metrics since this backend process last started — resets on deploy/restart.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="glass-card p-5">
          <div className="mb-2 flex items-center gap-2 text-slate-400">
            <Gauge size={16} />
            <span className="text-xs uppercase tracking-wide">Avg Response Time</span>
          </div>
          <p className="text-2xl font-bold text-slate-50">
            {health.request_metrics.average_response_time_ms != null
              ? `${health.request_metrics.average_response_time_ms} ms`
              : "—"}
          </p>
        </div>
        <div className="glass-card p-5">
          <div className="mb-2 flex items-center gap-2 text-slate-400">
            <Activity size={16} />
            <span className="text-xs uppercase tracking-wide">Error Rate</span>
          </div>
          <p className="text-2xl font-bold text-slate-50">
            {health.request_metrics.error_rate_percent != null ? `${health.request_metrics.error_rate_percent}%` : "—"}
          </p>
        </div>
        <div className="glass-card p-5">
          <div className="mb-2 flex items-center gap-2 text-slate-400">
            <Clock size={16} />
            <span className="text-xs uppercase tracking-wide">Requests (5 min)</span>
          </div>
          <p className="text-2xl font-bold text-slate-50">{health.request_metrics.requests_last_5_min}</p>
        </div>
        <div className="glass-card p-5">
          <div className="mb-2 flex items-center gap-2 text-slate-400">
            <Clock size={16} />
            <span className="text-xs uppercase tracking-wide">Uptime</span>
          </div>
          <p className="text-2xl font-bold text-slate-50">{formatUptime(health.uptime_seconds)}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="glass-card p-6">
          <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
            <Database size={16} className="text-slate-400" />
            Database Status
          </h2>
          <div className="flex items-center gap-2">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                health.database.status === "healthy" ? "bg-safe" : "bg-danger"
              }`}
            />
            <span className="text-sm text-slate-200">{health.database.message}</span>
          </div>
        </div>

        <div className="glass-card p-6">
          <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
            <HardDrive size={16} className="text-slate-400" />
            Memory Usage
          </h2>
          <EmptyState
            icon={HardDrive}
            title="Not available yet"
            description={health.memory.message}
          />
        </div>
      </div>

      <div className="glass-card p-6">
        <h2 className="mb-2 text-base font-semibold text-slate-100">Total requests observed</h2>
        <p className="text-2xl font-bold text-slate-50">{health.request_metrics.total_requests}</p>
        <p className="mt-1 text-xs text-slate-500">
          Tracked in-memory since process start — a bounded rolling window, not a persisted metrics store.
        </p>
      </div>
    </div>
  );
}
