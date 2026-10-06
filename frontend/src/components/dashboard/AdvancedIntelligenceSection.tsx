import {
  Activity,
  AlertTriangle,
  BarChart3,
  Bell,
  Clock,
  Fingerprint,
  Gauge,
  Globe2,
  KeyRound,
  LayoutGrid,
  Mail,
  QrCode,
  ScanSearch,
  Settings as SettingsIcon,
  Shield,
  ShieldQuestion,
  TrendingUp,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { DailyBarChart } from "@/components/dashboard/DailyBarChart";
import { RankedBarList } from "@/components/dashboard/RankedBarList";
import { ThreatHeatmap } from "@/components/dashboard/ThreatHeatmap";
import { EmptyState } from "@/components/common/EmptyState";
import { TrustScoreGauge } from "@/components/scanner/TrustScoreGauge";
import { UnifiedScanList } from "@/components/scanCenter/UnifiedScanList";
import { NOTIFICATION_ICON } from "@/lib/notifications";
import { extractErrorMessage } from "@/lib/errors";
import { formatRelativeDate } from "@/lib/risk";
import * as dashboardIntelService from "@/services/dashboardIntelService";
import type { DashboardIntelligence } from "@/types/dashboardIntel";
import type { RiskLevel } from "@/types/scan";

const RISK_SEGMENTS: { key: "safe" | "low_risk" | "suspicious" | "dangerous"; label: string; classes: string }[] = [
  { key: "safe", label: "Safe", classes: "bg-safe" },
  { key: "low_risk", label: "Low Risk", classes: "bg-brand-cyan" },
  { key: "suspicious", label: "Suspicious", classes: "bg-warning" },
  { key: "dangerous", label: "Dangerous", classes: "bg-danger" },
];

const QUICK_ACTIONS = [
  { label: "Scan a URL", to: "/dashboard/url-scanner", icon: ScanSearch },
  { label: "Scan an Email", to: "/dashboard/email-scanner", icon: Mail },
  { label: "Scan a QR Code", to: "/dashboard/qr-scanner", icon: QrCode },
  { label: "Threat Intelligence", to: "/dashboard/threat-intelligence", icon: Globe2 },
  { label: "Scan Center", to: "/dashboard/scan-center", icon: LayoutGrid },
  { label: "Settings", to: "/dashboard/settings", icon: SettingsIcon },
];

function scoreToRisk(score: number): RiskLevel {
  if (score >= 90) return "Safe";
  if (score >= 70) return "Low Risk";
  if (score >= 40) return "Suspicious";
  return "Dangerous";
}

function formatDuration(ms: number | null): string {
  if (ms == null) return "—";
  if (ms < 1000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
}

export function AdvancedIntelligenceSection() {
  const [data, setData] = useState<DashboardIntelligence | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    dashboardIntelService
      .getDashboardIntelligence()
      .then(setData)
      .catch((err) => setError(extractErrorMessage(err, "Could not load advanced dashboard intelligence.")))
      .finally(() => setIsLoading(false));
  }, []);

  if (error) {
    return <div className="glass-card border-danger/20 p-4 text-sm text-danger">{error}</div>;
  }

  const riskTotal = data
    ? data.risk_distribution.safe + data.risk_distribution.low_risk + data.risk_distribution.suspicious + data.risk_distribution.dangerous
    : 0;

  return (
    <div className="flex flex-col gap-6">
      <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
        <Gauge size={14} />
        Advanced Intelligence
      </h2>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="glass-card flex flex-col items-center justify-center gap-3 p-6">
          <h3 className="text-sm font-semibold text-slate-300">Overall Security Score</h3>
          {isLoading ? (
            <div className="h-40 w-40 animate-pulse rounded-full bg-white/[0.03]" />
          ) : data?.overall_security_score != null ? (
            <TrustScoreGauge score={data.overall_security_score} risk={scoreToRisk(data.overall_security_score)} size={140} />
          ) : (
            <p className="py-10 text-center text-sm text-slate-500">Run a scan to calculate your score.</p>
          )}
        </div>

        <div className="glass-card p-6 lg:col-span-2">
          <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
            <TrendingUp size={16} className="text-slate-400" />
            Threat Trend (14 days)
          </h3>
          {isLoading ? (
            <div className="h-32 animate-pulse rounded-lg bg-white/[0.03]" />
          ) : (
            <DailyBarChart data={data?.threat_trend ?? []} barClassName="bg-danger" />
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="glass-card p-6">
          <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
            <BarChart3 size={16} className="text-slate-400" />
            Weekly Activity
          </h3>
          {isLoading ? (
            <div className="h-32 animate-pulse rounded-lg bg-white/[0.03]" />
          ) : (
            <DailyBarChart data={data?.weekly_activity ?? []} />
          )}
        </div>
        <div className="glass-card p-6">
          <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
            <BarChart3 size={16} className="text-slate-400" />
            Monthly Activity
          </h3>
          {isLoading ? (
            <div className="h-32 animate-pulse rounded-lg bg-white/[0.03]" />
          ) : (
            <DailyBarChart data={data?.monthly_activity ?? []} />
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="glass-card p-6">
          <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
            <Shield size={16} className="text-slate-400" />
            Risk Distribution
          </h3>
          {isLoading ? (
            <div className="h-16 animate-pulse rounded-lg bg-white/[0.03]" />
          ) : riskTotal === 0 ? (
            <p className="py-6 text-center text-sm text-slate-500">No scans yet.</p>
          ) : (
            <div className="flex flex-col gap-4">
              <div className="flex h-3 w-full overflow-hidden rounded-full bg-white/5">
                {RISK_SEGMENTS.map((segment) => {
                  const count = data!.risk_distribution[segment.key];
                  const pct = (count / riskTotal) * 100;
                  if (pct <= 0) return null;
                  return <div key={segment.label} className={segment.classes} style={{ width: `${pct}%` }} />;
                })}
              </div>
              <div className="flex flex-wrap gap-x-5 gap-y-2">
                {RISK_SEGMENTS.map((segment) => (
                  <div key={segment.label} className="flex items-center gap-2 text-xs text-slate-400">
                    <span className={`h-2 w-2 rounded-full ${segment.classes}`} />
                    {segment.label} ({data!.risk_distribution[segment.key]})
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="glass-card p-6">
          <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
            <Activity size={16} className="text-slate-400" />
            Threat Heat Map (90 days)
          </h3>
          {isLoading ? (
            <div className="h-40 animate-pulse rounded-lg bg-white/[0.03]" />
          ) : (
            <ThreatHeatmap data={data?.threat_heatmap ?? []} />
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="glass-card p-6">
          <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
            <Globe2 size={16} className="text-slate-400" />
            Most Dangerous Domains
          </h3>
          {isLoading ? (
            <p className="py-6 text-center text-sm text-slate-500">Loading…</p>
          ) : (
            <RankedBarList
              items={(data?.most_dangerous_domains ?? []).map((d) => ({ label: d.domain, count: d.count }))}
              barClassName="bg-danger"
              emptyText="No dangerous domains detected yet."
            />
          )}
        </div>

        <div className="glass-card p-6">
          <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
            <KeyRound size={16} className="text-slate-400" />
            Most Common Keywords
          </h3>
          {isLoading ? (
            <p className="py-6 text-center text-sm text-slate-500">Loading…</p>
          ) : (
            <RankedBarList
              items={(data?.most_common_keywords ?? []).map((k) => ({ label: k.keyword, count: k.count }))}
              emptyText="No suspicious keywords detected yet."
            />
          )}
        </div>

        <div className="glass-card flex flex-col gap-4 p-6">
          <div>
            <h3 className="mb-2 flex items-center gap-2 text-base font-semibold text-slate-100">
              <Fingerprint size={16} className="text-slate-400" />
              Most Common Scanner
            </h3>
            <p className="text-2xl font-bold capitalize text-slate-50">
              {isLoading ? "—" : data?.most_common_scanner ?? "—"}
            </p>
          </div>
          <div className="border-t border-white/5 pt-4">
            <h3 className="mb-2 flex items-center gap-2 text-base font-semibold text-slate-100">
              <Clock size={16} className="text-slate-400" />
              Average Scan Duration
            </h3>
            <p className="text-2xl font-bold text-slate-50">
              {isLoading ? "—" : formatDuration(data?.average_scan_duration_ms ?? null)}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="glass-card p-6 lg:col-span-1">
          <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
            <ShieldQuestion size={16} className="text-slate-400" />
            Detection Accuracy
          </h3>
          <EmptyState
            icon={ShieldQuestion}
            title="Not available yet"
            description={data?.detection_accuracy.message ?? "Requires labeled ground-truth data to compute."}
          />
        </div>

        <div className="glass-card p-6 lg:col-span-1">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-base font-semibold text-slate-100">
              <Bell size={16} className="text-slate-400" />
              Recent Notifications
            </h3>
            <Link to="/dashboard/notifications" className="text-xs font-medium text-brand-cyan hover:underline">
              View all
            </Link>
          </div>
          {isLoading ? (
            <p className="py-6 text-center text-sm text-slate-500">Loading…</p>
          ) : !data?.recent_notifications.length ? (
            <p className="py-6 text-center text-sm text-slate-500">No notifications yet.</p>
          ) : (
            <ul className="flex flex-col divide-y divide-white/5">
              {data.recent_notifications.map((notification) => {
                const Icon = NOTIFICATION_ICON[notification.type];
                return (
                  <li key={notification.id} className="flex items-start gap-3 py-2.5 first:pt-0 last:pb-0">
                    <Icon size={14} className="mt-0.5 shrink-0 text-slate-500" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm text-slate-200">{notification.title}</p>
                      <p className="text-xs text-slate-600">{formatRelativeDate(notification.created_at)}</p>
                    </div>
                    {!notification.is_read && <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-cyan" />}
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <div className="glass-card p-6 lg:col-span-1">
          <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
            <AlertTriangle size={16} className="text-warning" />
            Recent Threat Timeline
          </h3>
          {isLoading ? (
            <p className="py-6 text-center text-sm text-slate-500">Loading…</p>
          ) : (
            <UnifiedScanList
              items={data?.recent_threat_timeline ?? []}
              emptyIcon={Shield}
              emptyTitle="No threats yet"
              emptyDescription="Suspicious and dangerous scans will show up here."
            />
          )}
        </div>
      </div>

      <div className="glass-card p-6">
        <h3 className="mb-4 text-base font-semibold text-slate-100">Quick Actions</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {QUICK_ACTIONS.map((action) => (
            <Link
              key={action.to}
              to={action.to}
              className="flex flex-col items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-4 text-center text-xs font-medium text-slate-300 transition-colors hover:border-brand-cyan/40 hover:bg-brand-cyan/10 hover:text-brand-cyan"
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
