import {
  Activity,
  AlertTriangle,
  Bell,
  Database,
  LayoutGrid,
  LogIn,
  Puzzle,
  Radio,
  Shield,
  ShieldCheck,
  Users,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { StatCard } from "@/components/dashboard/StatCard";
import { UnifiedScanList } from "@/components/scanCenter/UnifiedScanList";
import { EmptyState } from "@/components/common/EmptyState";
import { formatRelativeDate } from "@/lib/risk";
import { extractErrorMessage } from "@/lib/errors";
import * as adminService from "@/services/adminService";
import type { SystemOverview } from "@/types/admin";

const QUICK_ACTIONS = [
  { label: "Manage Users", to: "/admin/users", icon: Users },
  { label: "Manage Scans", to: "/admin/scans", icon: LayoutGrid },
  { label: "Blacklist", to: "/admin/blacklist", icon: Shield },
  { label: "System Health", to: "/admin/system", icon: Activity },
];

// Live-ish active-user counter: reads the same session data already shown
// on /admin/threat-intel via /admin/stats. 30s keeps it "live" without
// hammering the platform-wide aggregation it's bundled with on every keystroke.
const ACTIVE_USERS_POLL_MS = 30_000;

export function AdminOverviewPage() {
  const [data, setData] = useState<SystemOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [activeUsers, setActiveUsers] = useState<{ count: number; window_minutes: number } | null>(null);

  useEffect(() => {
    adminService
      .getSystemOverview()
      .then(setData)
      .catch((err) => setError(extractErrorMessage(err, "Could not load the system overview.")))
      .finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    let cancelled = false;
    const poll = () => {
      adminService
        .getStats()
        .then((stats) => {
          if (!cancelled) setActiveUsers(stats.active_users);
        })
        .catch(() => {
          /* silent — this widget degrades to its loading state, not a page-level error */
        });
    };
    poll();
    const interval = setInterval(poll, ACTIVE_USERS_POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-slate-50">System Overview</h1>
            <p className="mt-1 text-sm text-slate-400">Platform-wide status across every CyberShield account.</p>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-sm">
            <Radio size={14} className="animate-pulse text-safe" />
            <span className="font-semibold text-slate-100">{activeUsers ? activeUsers.count : "—"}</span>
            <span className="text-slate-400">
              online now (active in the last {activeUsers?.window_minutes ?? 15} min)
            </span>
          </div>
        </div>
      </div>

      {error && <div className="glass-card border-danger/20 p-4 text-sm text-danger">{error}</div>}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Users} label="Total Users" value={isLoading ? "—" : String(data?.users.total ?? 0)} accent="blue" />
        <StatCard
          icon={ShieldCheck}
          label="Active Users"
          value={isLoading ? "—" : String(data?.users.active ?? 0)}
          accent="safe"
        />
        <StatCard
          icon={AlertTriangle}
          label="Dangerous Scans"
          value={isLoading ? "—" : String(data?.scans.dangerous_count ?? 0)}
          accent="danger"
        />
        <StatCard
          icon={Puzzle}
          label="Extension Scans"
          value={isLoading ? "—" : String(data?.extension_activity.scans_recorded ?? 0)}
          accent="cyan"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="glass-card p-6">
          <h2 className="mb-4 text-base font-semibold text-slate-100">Users</h2>
          {isLoading ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : (
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div><dt className="text-slate-500">Active</dt><dd className="text-slate-200">{data?.users.active}</dd></div>
              <div><dt className="text-slate-500">Inactive</dt><dd className="text-slate-200">{data?.users.inactive}</dd></div>
              <div><dt className="text-slate-500">Verified</dt><dd className="text-slate-200">{data?.users.verified}</dd></div>
              <div><dt className="text-slate-500">Admins</dt><dd className="text-slate-200">{data?.users.admins}</dd></div>
            </dl>
          )}
        </div>

        <div className="glass-card p-6">
          <h2 className="mb-4 text-base font-semibold text-slate-100">Scans (platform-wide)</h2>
          {isLoading ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : (
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div><dt className="text-slate-500">Total</dt><dd className="text-slate-200">{data?.scans.total_scans}</dd></div>
              <div><dt className="text-slate-500">URL</dt><dd className="text-slate-200">{data?.scans.by_scanner_type.url}</dd></div>
              <div><dt className="text-slate-500">Email</dt><dd className="text-slate-200">{data?.scans.by_scanner_type.email}</dd></div>
              <div><dt className="text-slate-500">QR</dt><dd className="text-slate-200">{data?.scans.by_scanner_type.qr}</dd></div>
            </dl>
          )}
        </div>

        <div className="glass-card p-6">
          <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
            <Database size={16} className="text-slate-400" />
            System Health
          </h2>
          {isLoading ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : (
            <div className="flex flex-col gap-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Database</span>
                <span className={data?.system_health.database.status === "healthy" ? "text-safe" : "text-danger"}>
                  {data?.system_health.database.status}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Avg response time</span>
                <span className="text-slate-200">
                  {data?.system_health.request_metrics.average_response_time_ms != null
                    ? `${data.system_health.request_metrics.average_response_time_ms} ms`
                    : "—"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Error rate</span>
                <span className="text-slate-200">
                  {data?.system_health.request_metrics.error_rate_percent != null
                    ? `${data.system_health.request_metrics.error_rate_percent}%`
                    : "—"}
                </span>
              </div>
              <Link to="/admin/system" className="mt-1 text-xs font-medium text-brand-cyan hover:underline">
                View full system health →
              </Link>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="glass-card p-6">
          <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
            <AlertTriangle size={16} className="text-warning" />
            Latest Threats
          </h2>
          {isLoading ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : (
            <UnifiedScanList
              items={data?.scans.latest_threats ?? []}
              emptyIcon={ShieldCheck}
              emptyTitle="No threats detected"
              emptyDescription="Suspicious and dangerous scans across the platform will show up here."
            />
          )}
        </div>

        <div className="glass-card p-6">
          <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
            <LogIn size={16} className="text-slate-400" />
            Recent Logins
          </h2>
          {isLoading ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : !data?.recent_logins.length ? (
            <EmptyState icon={LogIn} title="No logins yet" description="Recent sign-ins will show up here." />
          ) : (
            <ul className="flex flex-col divide-y divide-white/5">
              {data.recent_logins.map((log) => (
                <li key={log.id} className="flex items-center justify-between py-2.5 first:pt-0 last:pb-0 text-sm">
                  <span className="text-slate-300">{(log.details?.email as string) ?? log.user_id ?? "Unknown"}</span>
                  <span className="text-xs text-slate-500">{formatRelativeDate(log.created_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="glass-card p-6">
        <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
          <Bell size={16} className="text-slate-400" />
          Notifications sent (platform-wide)
        </h2>
        <p className="text-2xl font-bold text-slate-50">{isLoading ? "—" : data?.notifications_sent}</p>
      </div>

      <div className="glass-card p-6">
        <h2 className="mb-4 text-base font-semibold text-slate-100">Quick Actions</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {QUICK_ACTIONS.map((action) => (
            <Link
              key={action.to}
              to={action.to}
              className="flex flex-col items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-4 text-center text-xs font-medium text-slate-300 transition-colors hover:border-danger/40 hover:bg-danger/10 hover:text-danger"
            >
              <action.icon size={18} />
              {action.label}
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
