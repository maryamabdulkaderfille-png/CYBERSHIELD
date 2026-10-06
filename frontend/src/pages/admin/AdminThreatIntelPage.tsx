import {
  AlertOctagon,
  Ban,
  BarChart3,
  Fingerprint,
  Globe2,
  KeyRound,
  Radar,
  Shield,
  ShieldAlert,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

import { DailyBarChart } from "@/components/dashboard/DailyBarChart";
import { RankedBarList } from "@/components/dashboard/RankedBarList";
import { StatCard } from "@/components/dashboard/StatCard";
import { extractErrorMessage } from "@/lib/errors";
import { formatRelativeDate } from "@/lib/risk";
import * as adminService from "@/services/adminService";
import type { AdminStats } from "@/types/admin";

function SectionCard({ title, icon: Icon, children }: { title: string; icon: typeof Shield; children: ReactNode }) {
  return (
    <div className="glass-card p-6">
      <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
        <Icon size={16} className="text-slate-400" />
        {title}
      </h3>
      {children}
    </div>
  );
}

/** Admin-gated view over the same platform-wide threat data every user can
 * already see at /dashboard/threat-intel (via /threats) — this page exists
 * so admin tooling has it alongside System Overview/Users/etc. behind one
 * permission-gated call (/admin/stats), not a second detection pipeline. */
export function AdminThreatIntelPage() {
  const [data, setData] = useState<AdminStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    adminService
      .getStats()
      .then(setData)
      .catch((err) => setError(extractErrorMessage(err, "Could not load threat intelligence.")))
      .finally(() => setIsLoading(false));
  }, []);

  const summary = data?.threat_intelligence;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-50">Threat Intelligence</h1>
        <p className="mt-1 text-sm text-slate-400">Platform-wide threat patterns derived from every user's scans.</p>
      </div>

      {error && <div className="glass-card border-danger/20 p-4 text-sm text-danger">{error}</div>}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={Globe2}
          label="Total Scans (Platform)"
          value={isLoading ? "—" : String(summary?.threat_statistics.total_scans ?? 0)}
          accent="blue"
        />
        <StatCard
          icon={ShieldAlert}
          label="Dangerous Scans"
          value={isLoading ? "—" : String(summary?.threat_statistics.dangerous_count ?? 0)}
          accent="danger"
        />
        <StatCard
          icon={AlertOctagon}
          label="Suspicious Scans"
          value={isLoading ? "—" : String(summary?.threat_statistics.suspicious_count ?? 0)}
          accent="cyan"
        />
        <StatCard
          icon={Ban}
          label="Blacklisted Domains"
          value={isLoading ? "—" : String(summary?.threat_statistics.blacklisted_domains ?? 0)}
          accent="safe"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SectionCard title="Detection Trend (14 days)" icon={BarChart3}>
          {isLoading ? (
            <div className="h-32 animate-pulse rounded-lg bg-white/[0.03]" />
          ) : (
            <DailyBarChart data={summary?.detection_trends ?? []} barClassName="bg-danger" />
          )}
        </SectionCard>

        <SectionCard title="Severity Distribution" icon={Radar}>
          {isLoading || !summary || summary.threat_statistics.total_scans === 0 ? (
            <p className="py-8 text-center text-sm text-slate-500">No scans yet.</p>
          ) : (
            <RankedBarList
              items={[
                { label: "Safe", count: summary.severity_distribution.safe },
                { label: "Low Risk", count: summary.severity_distribution.low_risk },
                { label: "Suspicious", count: summary.severity_distribution.suspicious },
                { label: "Dangerous", count: summary.severity_distribution.dangerous },
              ]}
              barClassName="bg-warning"
            />
          )}
        </SectionCard>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <SectionCard title="Known Phishing Domains" icon={Ban}>
          {isLoading ? (
            <p className="py-6 text-center text-sm text-slate-500">Loading…</p>
          ) : !summary?.known_phishing_domains.length ? (
            <p className="py-6 text-center text-sm text-slate-500">No blacklisted domains recorded yet.</p>
          ) : (
            <ul className="flex flex-col gap-2.5">
              {summary.known_phishing_domains.map((entry) => (
                <li key={entry.domain} className="flex flex-col text-sm">
                  <span className="truncate font-medium text-slate-200">{entry.domain}</span>
                  <span className="text-xs text-slate-500">{entry.reason}</span>
                </li>
              ))}
            </ul>
          )}
        </SectionCard>

        <SectionCard title="Recently Blocked Domains" icon={Shield}>
          {isLoading ? (
            <p className="py-6 text-center text-sm text-slate-500">Loading…</p>
          ) : !summary?.recently_blocked_domains.length ? (
            <p className="py-6 text-center text-sm text-slate-500">No blocked domains yet.</p>
          ) : (
            <ul className="flex flex-col gap-2.5">
              {summary.recently_blocked_domains.map((entry, idx) => (
                <li key={`${entry.domain}-${idx}`} className="flex flex-col text-sm">
                  <span className="truncate font-medium text-slate-200">{entry.domain}</span>
                  <span className="text-xs text-slate-500">{formatRelativeDate(entry.blocked_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </SectionCard>

        <SectionCard title="Top Targeted Brands" icon={Fingerprint}>
          {isLoading ? (
            <p className="py-6 text-center text-sm text-slate-500">Loading…</p>
          ) : (
            <RankedBarList
              items={(summary?.top_targeted_brands ?? []).map((b) => ({ label: b.brand, count: b.count }))}
              barClassName="bg-danger"
              emptyText="No brand impersonation detected yet."
            />
          )}
        </SectionCard>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SectionCard title="Most Common Keywords" icon={KeyRound}>
          {isLoading ? (
            <p className="py-6 text-center text-sm text-slate-500">Loading…</p>
          ) : (
            <RankedBarList
              items={(summary?.most_common_keywords ?? []).map((k) => ({ label: k.keyword, count: k.count }))}
              emptyText="No suspicious keywords detected yet."
            />
          )}
        </SectionCard>

        <SectionCard title="Attack Categories" icon={Radar}>
          {isLoading ? (
            <p className="py-6 text-center text-sm text-slate-500">Loading…</p>
          ) : (
            <RankedBarList
              items={(summary?.attack_categories ?? []).map((c) => ({ label: c.category, count: c.count }))}
              barClassName="bg-brand-blue"
              emptyText="No detection rules have triggered yet."
            />
          )}
        </SectionCard>
      </div>
    </div>
  );
}
