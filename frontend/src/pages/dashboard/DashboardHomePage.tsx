import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  LayoutGrid,
  Mail,
  ScanLine,
  ShieldCheck,
  ShieldX,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "@/components/common/EmptyState";
import { AdvancedIntelligenceSection } from "@/components/dashboard/AdvancedIntelligenceSection";
import { AreaChart } from "@/components/dashboard/AreaChart";
import { DateRangeFilter } from "@/components/dashboard/DateRangeFilter";
import { DonutChart } from "@/components/dashboard/DonutChart";
import { StatCard } from "@/components/dashboard/StatCard";
import { ProtectionStatsSection } from "@/components/protection/ProtectionStatsSection";
import { RecentEmailScansList, ViewAllEmailHistoryLink } from "@/components/emailScanner/RecentEmailScansList";
import { UnifiedScanList } from "@/components/scanCenter/UnifiedScanList";
import { RecentScansList, ViewAllHistoryLink } from "@/components/scanner/RecentScansList";
import { useAuth } from "@/context/AuthContext";
import { extractErrorMessage } from "@/lib/errors";
import * as emailScanService from "@/services/emailScanService";
import * as scanCenterService from "@/services/scanCenterService";
import * as scanService from "@/services/scanService";
import type { EmailDashboardStats } from "@/types/emailScan";
import type { DashboardStats } from "@/types/scan";
import type {
  DateRangeKey,
  UnifiedScanItem,
  UnifiedScanStats,
  UnifiedScanStatsRange,
  UnifiedScanStatsTrend,
} from "@/types/unifiedScan";

const DISTRIBUTION_SEGMENTS: { key: keyof DashboardStats; label: string; classes: string }[] = [
  { key: "safe_count", label: "Safe", classes: "bg-safe" },
  { key: "low_risk_count", label: "Low Risk", classes: "bg-brand-cyan" },
  { key: "suspicious_count", label: "Suspicious", classes: "bg-warning" },
  { key: "dangerous_count", label: "Dangerous", classes: "bg-danger" },
];

const RISK_DONUT_COLORS: { key: keyof UnifiedScanStatsRange; label: string; classes: string; hex: string }[] = [
  { key: "safe_count", label: "Safe", classes: "bg-safe", hex: "#22c55e" },
  { key: "low_risk_count", label: "Low Risk", classes: "bg-brand-cyan", hex: "#22d3ee" },
  { key: "suspicious_count", label: "Suspicious", classes: "bg-warning", hex: "#eab308" },
  { key: "dangerous_count", label: "Dangerous", classes: "bg-danger", hex: "#ef4444" },
];

function rangeCutoff(range: DateRangeKey): Date | null {
  const now = new Date();
  if (range === "today") return new Date(now.getFullYear(), now.getMonth(), now.getDate());
  if (range === "7d") return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  if (range === "30d") return new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
  return null;
}

function filterByRange(items: UnifiedScanItem[], range: DateRangeKey): UnifiedScanItem[] {
  const cutoff = rangeCutoff(range);
  if (!cutoff) return items;
  return items.filter((item) => new Date(item.scan_date) >= cutoff);
}

export function DashboardHomePage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [emailStats, setEmailStats] = useState<EmailDashboardStats | null>(null);
  const [isLoadingEmailStats, setIsLoadingEmailStats] = useState(true);
  const [emailError, setEmailError] = useState<string | null>(null);

  const [unifiedStats, setUnifiedStats] = useState<UnifiedScanStats | null>(null);
  const [isLoadingUnified, setIsLoadingUnified] = useState(true);
  const [unifiedError, setUnifiedError] = useState<string | null>(null);

  const [dateRange, setDateRange] = useState<DateRangeKey>("all");
  const [rangeStats, setRangeStats] = useState<UnifiedScanStatsRange | null>(null);
  const [isLoadingRange, setIsLoadingRange] = useState(true);

  const [trendStats, setTrendStats] = useState<UnifiedScanStatsTrend | null>(null);

  useEffect(() => {
    scanService
      .getDashboardStats()
      .then(setStats)
      .catch((err) => setError(extractErrorMessage(err, "Could not load your dashboard stats.")))
      .finally(() => setIsLoading(false));

    emailScanService
      .getEmailDashboardStats()
      .then(setEmailStats)
      .catch((err) => setEmailError(extractErrorMessage(err, "Could not load your email scan stats.")))
      .finally(() => setIsLoadingEmailStats(false));

    scanCenterService
      .getUnifiedStats()
      .then(setUnifiedStats)
      .catch((err) => setUnifiedError(extractErrorMessage(err, "Could not load your combined scan stats.")))
      .finally(() => setIsLoadingUnified(false));

    scanCenterService.getUnifiedStatsTrend().then(setTrendStats).catch(() => setTrendStats(null));
  }, []);

  useEffect(() => {
    setIsLoadingRange(true);
    scanCenterService
      .getUnifiedStatsRange(dateRange)
      .then(setRangeStats)
      .catch(() => setRangeStats(null))
      .finally(() => setIsLoadingRange(false));
  }, [dateRange]);

  const threatsDetected = stats ? stats.suspicious_count + stats.dangerous_count : 0;
  const highRiskEmails = emailStats ? emailStats.suspicious_count + emailStats.dangerous_count : 0;
  const rangeThreats = rangeStats ? rangeStats.suspicious_count + rangeStats.dangerous_count : 0;

  const trendSparkline = {
    total: trendStats?.total_scans.series.map((p) => p.count) ?? [],
    safe: trendStats?.safe_count.series.map((p) => p.count) ?? [],
    threats: trendStats?.threats_count.series.map((p) => p.count) ?? [],
    trust: trendStats?.average_trust_score.series.map((p) => p.value) ?? [],
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="glass-card relative overflow-hidden p-6">
        <video
          aria-hidden="true"
          autoPlay
          muted
          loop
          playsInline
          preload="none"
          className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-40"
          src="/13770658_3840_2160_30fps.mp4"
        />
        {/* Darkens the background video so the welcome text keeps the same
            contrast as every other glass-card heading on this page. */}
        <div className="absolute inset-0 bg-navy-950/50" aria-hidden="true" />
        <div className="relative">
          <h1 className="text-2xl font-bold text-slate-50">Welcome back, {user?.full_name?.split(" ")[0]}</h1>
          <p className="mt-1 text-sm text-slate-400">Here's your security overview.</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
          <LayoutGrid size={14} />
          Unified Overview
          <span className="relative flex h-2 w-2" title="Scanning is continuous">
            <span className="absolute inline-flex h-full w-full animate-pulse-slow rounded-full bg-safe opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-safe" />
          </span>
        </h2>
        <div className="flex flex-wrap items-center gap-3">
          <DateRangeFilter value={dateRange} onChange={setDateRange} />
          <Link to="/dashboard/scan-center" className="text-xs font-medium text-brand-cyan hover:underline">
            Open Scan Center
          </Link>
        </div>
      </div>

      {unifiedError && (
        <div className="glass-card border-danger/20 p-4 text-sm text-danger">{unifiedError}</div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={Activity}
          label="Total Scans (All Types)"
          value={isLoadingRange ? "—" : String(rangeStats?.total_scans ?? 0)}
          accent="blue"
          trend={{
            deltaPct: trendStats?.total_scans.delta_pct ?? null,
            upIsGood: true,
            sparkline: trendSparkline.total,
          }}
        />
        <StatCard
          icon={ShieldCheck}
          label="Safe Results"
          value={isLoadingRange ? "—" : String(rangeStats?.safe_count ?? 0)}
          accent="safe"
          trend={{
            deltaPct: trendStats?.safe_count.delta_pct ?? null,
            upIsGood: true,
            sparkline: trendSparkline.safe,
          }}
        />
        <StatCard
          icon={ShieldX}
          label="Threats Detected"
          value={isLoadingRange ? "—" : String(rangeThreats)}
          accent="danger"
          trend={{
            deltaPct: trendStats?.threats_count.delta_pct ?? null,
            upIsGood: false,
            sparkline: trendSparkline.threats,
          }}
        />
        <StatCard
          icon={TrendingUp}
          label="Average Trust Score"
          value={
            isLoadingRange
              ? "—"
              : rangeStats?.average_trust_score != null
                ? String(rangeStats.average_trust_score)
                : "—"
          }
          accent="cyan"
          trend={{
            deltaPct: trendStats?.average_trust_score.delta_pct ?? null,
            upIsGood: true,
            sparkline: trendSparkline.trust,
          }}
        />
      </div>

      {!isLoadingRange && rangeStats && rangeStats.total_scans > 0 && (
        <div className="flex flex-wrap gap-3 text-xs text-slate-400">
          <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1">
            URL: {rangeStats.by_scanner_type.url}
          </span>
          <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1">
            Email: {rangeStats.by_scanner_type.email}
          </span>
          <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1">
            QR: {rangeStats.by_scanner_type.qr}
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.05 }}
          className="glass-card p-6"
        >
          <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
            <ShieldCheck size={16} className="text-slate-400" />
            Result Breakdown
          </h3>
          {isLoadingRange ? (
            <div className="h-40 animate-pulse rounded-lg bg-white/[0.03]" />
          ) : rangeStats && rangeStats.total_scans > 0 ? (
            <DonutChart
              segments={RISK_DONUT_COLORS.map((s) => ({
                label: s.label,
                value: rangeStats[s.key] as number,
                colorClassName: s.classes,
                colorHex: s.hex,
              }))}
              centerLabel="scans"
              centerValue={String(rangeStats.total_scans)}
            />
          ) : (
            <p className="py-10 text-center text-sm text-slate-500">No scans in this range yet.</p>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="glass-card p-6 lg:col-span-2"
        >
          <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
            <TrendingUp size={16} className="text-slate-400" />
            Scan Volume (14 days)
          </h3>
          {trendStats ? (
            <AreaChart data={trendStats.total_scans.series} />
          ) : (
            <div className="h-40 animate-pulse rounded-lg bg-white/[0.03]" />
          )}
        </motion.div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="glass-card p-6">
          <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
            <Activity size={16} className="text-slate-400" />
            Recent Scans
          </h3>
          {isLoadingUnified ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : (
            <UnifiedScanList
              items={filterByRange(unifiedStats?.recent_scans ?? [], dateRange)}
              emptyIcon={LayoutGrid}
              emptyTitle="No scans yet"
              emptyDescription="Run a URL, email, or QR scan to see it here."
            />
          )}
        </div>

        <div className="glass-card p-6">
          <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
            <AlertTriangle size={16} className="text-warning" />
            Latest Threats
          </h3>
          {isLoadingUnified ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : (
            <UnifiedScanList
              items={filterByRange(unifiedStats?.latest_threats ?? [], dateRange)}
              emptyIcon={ShieldCheck}
              emptyTitle="No threats detected"
              emptyDescription="Suspicious and dangerous scans will show up here."
            />
          )}
        </div>

        <div className="glass-card p-6">
          <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
            <TrendingDown size={16} className="text-danger" />
            Top Risks
          </h3>
          {isLoadingUnified ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : (
            <UnifiedScanList
              items={filterByRange(unifiedStats?.top_risks ?? [], dateRange)}
              emptyIcon={TrendingDown}
              emptyTitle="Nothing to show"
              emptyDescription="Your lowest-scoring scans will show up here."
            />
          )}
        </div>
      </div>

      {error && (
        <div className="glass-card border-danger/20 p-4 text-sm text-danger">{error}</div>
      )}

      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">URL Security</h2>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Activity} label="Total Scans" value={isLoading ? "—" : String(stats?.total_scans ?? 0)} accent="blue" />
        <StatCard
          icon={ShieldCheck}
          label="Safe Websites"
          value={isLoading ? "—" : String(stats?.safe_count ?? 0)}
          accent="safe"
        />
        <StatCard
          icon={ShieldX}
          label="Threats Detected"
          value={isLoading ? "—" : String(threatsDetected)}
          accent="danger"
        />
        <StatCard
          icon={TrendingUp}
          label="Average Trust Score"
          value={isLoading ? "—" : stats?.average_trust_score != null ? String(stats.average_trust_score) : "—"}
          accent="cyan"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="glass-card p-6 lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-100">Risk distribution</h2>
            <BarChart3 size={18} className="text-slate-500" />
          </div>

          {!isLoading && stats && stats.total_scans > 0 ? (
            <div className="flex flex-col gap-4">
              <div className="flex h-3 w-full overflow-hidden rounded-full bg-white/5">
                {DISTRIBUTION_SEGMENTS.map((segment) => {
                  const count = stats[segment.key] as number;
                  const pct = (count / stats.total_scans) * 100;
                  if (pct <= 0) return null;
                  return <div key={segment.label} className={segment.classes} style={{ width: `${pct}%` }} />;
                })}
              </div>
              <div className="flex flex-wrap gap-x-5 gap-y-2">
                {DISTRIBUTION_SEGMENTS.map((segment) => (
                  <div key={segment.label} className="flex items-center gap-2 text-xs text-slate-400">
                    <span className={`h-2 w-2 rounded-full ${segment.classes}`} />
                    {segment.label} ({stats[segment.key] as number})
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <EmptyState
              icon={ScanLine}
              title="No scans yet"
              description="Once you start scanning URLs, your risk breakdown will appear here."
              action={
                <Link to="/dashboard/url-scanner" className="btn-primary mt-2">
                  Scan a URL
                </Link>
              }
            />
          )}
        </div>

        <div className="glass-card p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-100">Recent activity</h2>
            {!isLoading && stats && stats.recent_scans.length > 0 && <ViewAllHistoryLink />}
          </div>
          {isLoading ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : (
            <RecentScansList
              scans={stats?.recent_scans ?? []}
              emptyDescription="Your scan history will show up here once you scan a URL."
            />
          )}
        </div>
      </div>

      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Email Security</h2>

      {emailError && (
        <div className="glass-card border-danger/20 p-4 text-sm text-danger">{emailError}</div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={Mail}
          label="Emails Scanned"
          value={isLoadingEmailStats ? "—" : String(emailStats?.total_emails_scanned ?? 0)}
          accent="blue"
        />
        <StatCard
          icon={ShieldCheck}
          label="Safe Emails"
          value={isLoadingEmailStats ? "—" : String(emailStats?.safe_count ?? 0)}
          accent="safe"
        />
        <StatCard
          icon={ShieldX}
          label="High Risk Emails"
          value={isLoadingEmailStats ? "—" : String(highRiskEmails)}
          accent="danger"
        />
        <StatCard
          icon={TrendingUp}
          label="Average Email Trust Score"
          value={
            isLoadingEmailStats
              ? "—"
              : emailStats?.average_trust_score != null
                ? String(emailStats.average_trust_score)
                : "—"
          }
          accent="cyan"
        />
      </div>

      <div className="glass-card p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-base font-semibold text-slate-100">Recent email activity</h3>
          {!isLoadingEmailStats && emailStats && emailStats.recent_scans.length > 0 && <ViewAllEmailHistoryLink />}
        </div>
        {isLoadingEmailStats ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : (
          <RecentEmailScansList
            scans={emailStats?.recent_scans ?? []}
            emptyDescription="Your email scan history will show up here once you analyze an email."
          />
        )}
      </div>

      <AdvancedIntelligenceSection />

      <ProtectionStatsSection />
    </div>
  );
}
