import {
  AlertOctagon,
  ArrowUpDown,
  Ban,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  Download,
  Fingerprint,
  Globe2,
  KeyRound,
  Radar,
  Search,
  Shield,
  ShieldAlert,
} from "lucide-react";
import { useEffect, useState, type FormEvent, type ReactNode } from "react";

import { StatCard } from "@/components/dashboard/StatCard";
import { DailyBarChart } from "@/components/dashboard/DailyBarChart";
import { RankedBarList } from "@/components/dashboard/RankedBarList";
import { Badge } from "@/components/common/Badge";
import { EmptyState } from "@/components/common/EmptyState";
import { useToast } from "@/context/ToastContext";
import { extractErrorMessage } from "@/lib/errors";
import { formatRelativeDate, RISK_VARIANT } from "@/lib/risk";
import * as threatIntelService from "@/services/threatIntelService";
import type { RiskLevel } from "@/types/scan";
import type { ThreatIntelligenceSummary } from "@/types/threatIntel";

const PER_PAGE = 10;
const RISK_FILTERS: (RiskLevel | "All")[] = ["All", "Safe", "Low Risk", "Suspicious", "Dangerous"];

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

export function ThreatIntelligencePage() {
  const { showToast } = useToast();
  const [summary, setSummary] = useState<ThreatIntelligenceSummary | null>(null);
  const [isLoadingSummary, setIsLoadingSummary] = useState(true);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const [items, setItems] = useState<Awaited<ReturnType<typeof threatIntelService.getThreatDomains>>["items"]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [riskFilter, setRiskFilter] = useState<RiskLevel | "All">("All");
  const [sortBy, setSortBy] = useState<"count" | "last_seen" | "domain">("count");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [isLoadingDomains, setIsLoadingDomains] = useState(true);
  const [domainsError, setDomainsError] = useState<string | null>(null);

  useEffect(() => {
    threatIntelService
      .getThreatIntelligenceSummary()
      .then(setSummary)
      .catch((err) => setSummaryError(extractErrorMessage(err, "Could not load threat intelligence.")))
      .finally(() => setIsLoadingSummary(false));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setIsLoadingDomains(true);
    threatIntelService
      .getThreatDomains({
        page,
        per_page: PER_PAGE,
        search: search || undefined,
        risk_level: riskFilter === "All" ? undefined : riskFilter,
        sort_by: sortBy,
        sort_dir: sortDir,
      })
      .then((response) => {
        if (cancelled) return;
        setItems(response.items);
        setTotalPages(response.total_pages);
        setTotal(response.total);
      })
      .catch((err) => {
        if (!cancelled) setDomainsError(extractErrorMessage(err, "Could not load the domain feed."));
      })
      .finally(() => {
        if (!cancelled) setIsLoadingDomains(false);
      });
    return () => {
      cancelled = true;
    };
  }, [page, search, riskFilter, sortBy, sortDir]);

  const toggleSort = (column: "count" | "last_seen" | "domain") => {
    if (sortBy === column) {
      setSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(column);
      setSortDir("desc");
    }
  };

  const handleSearchSubmit = (event: FormEvent) => {
    event.preventDefault();
    setPage(1);
    setSearch(searchInput.trim());
  };

  const handleExport = async () => {
    try {
      await threatIntelService.exportThreatIntelligence();
    } catch (err) {
      showToast(extractErrorMessage(err, "Threat intelligence export is coming in a future update."), "info");
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-50">Threat Intelligence Center</h1>
          <p className="mt-1 text-sm text-slate-400">
            Platform-wide threat patterns derived from every CyberShield user's scans.
          </p>
        </div>
        <button onClick={handleExport} className="btn-secondary">
          <Download size={16} />
          Export
        </button>
      </div>

      {summaryError && <div className="glass-card border-danger/20 p-4 text-sm text-danger">{summaryError}</div>}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={Globe2}
          label="Total Scans (Platform)"
          value={isLoadingSummary ? "—" : String(summary?.threat_statistics.total_scans ?? 0)}
          accent="blue"
        />
        <StatCard
          icon={ShieldAlert}
          label="Dangerous Scans"
          value={isLoadingSummary ? "—" : String(summary?.threat_statistics.dangerous_count ?? 0)}
          accent="danger"
        />
        <StatCard
          icon={AlertOctagon}
          label="Suspicious Scans"
          value={isLoadingSummary ? "—" : String(summary?.threat_statistics.suspicious_count ?? 0)}
          accent="cyan"
        />
        <StatCard
          icon={Ban}
          label="Blacklisted Domains"
          value={isLoadingSummary ? "—" : String(summary?.threat_statistics.blacklisted_domains ?? 0)}
          accent="safe"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SectionCard title="Detection Trend (14 days)" icon={BarChart3}>
          {isLoadingSummary ? (
            <div className="h-32 animate-pulse rounded-lg bg-white/[0.03]" />
          ) : (
            <DailyBarChart data={summary?.detection_trends ?? []} barClassName="bg-danger" />
          )}
        </SectionCard>

        <SectionCard title="Severity Distribution" icon={Radar}>
          {isLoadingSummary || !summary || summary.threat_statistics.total_scans === 0 ? (
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
          {isLoadingSummary ? (
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
          {isLoadingSummary ? (
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
          {isLoadingSummary ? (
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
          {isLoadingSummary ? (
            <p className="py-6 text-center text-sm text-slate-500">Loading…</p>
          ) : (
            <RankedBarList
              items={(summary?.most_common_keywords ?? []).map((k) => ({ label: k.keyword, count: k.count }))}
              emptyText="No suspicious keywords detected yet."
            />
          )}
        </SectionCard>

        <SectionCard title="Attack Categories" icon={Radar}>
          {isLoadingSummary ? (
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

      {summary && (
        <div className="glass-card border-brand-cyan/20 p-5 text-sm text-slate-400">
          <p className="font-medium text-slate-200">Threat Feed Architecture</p>
          <p className="mt-1">{summary.threat_feed_architecture.message}</p>
          <p className="mt-1 text-xs text-slate-500">
            Current provider: <span className="font-mono">{summary.threat_feed_architecture.provider}</span> · Live
            external feed: {summary.threat_feed_architecture.live_feed_enabled ? "enabled" : "not yet enabled"}
          </p>
        </div>
      )}

      <div>
        <h2 className="mb-4 text-lg font-semibold text-slate-100">All Observed Domains</h2>

        <div className="glass-card flex flex-col gap-4 p-6">
          <div className="flex flex-col gap-3 sm:flex-row">
            <form onSubmit={handleSearchSubmit} className="relative flex-1">
              <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Search domains…"
                className="input-field pl-10"
              />
            </form>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {RISK_FILTERS.map((filter) => (
              <button
                key={filter}
                onClick={() => {
                  setRiskFilter(filter);
                  setPage(1);
                }}
                className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                  riskFilter === filter
                    ? "border-brand-cyan/50 bg-brand-cyan/10 text-brand-cyan"
                    : "border-white/10 bg-white/[0.03] text-slate-400 hover:text-slate-200"
                }`}
              >
                {filter}
              </button>
            ))}
          </div>
        </div>

        <div className="glass-card mt-4 p-6">
          {domainsError ? (
            <p className="text-sm text-danger">{domainsError}</p>
          ) : isLoadingDomains ? (
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-12 animate-pulse rounded-lg bg-white/[0.03]" />
              ))}
            </div>
          ) : items.length === 0 ? (
            <EmptyState icon={Globe2} title="No domains found" description="Try a different search term or filter." />
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-500">
                      <th className="pb-3 pr-4 font-medium">
                        <button onClick={() => toggleSort("domain")} className="inline-flex items-center gap-1">
                          Domain <ArrowUpDown size={12} />
                        </button>
                      </th>
                      <th className="pb-3 pr-4 font-medium">
                        <button onClick={() => toggleSort("count")} className="inline-flex items-center gap-1">
                          Occurrences <ArrowUpDown size={12} />
                        </button>
                      </th>
                      <th className="pb-3 pr-4 font-medium">Risk Level</th>
                      <th className="pb-3 pr-4 font-medium">Blacklisted</th>
                      <th className="pb-3 font-medium">
                        <button onClick={() => toggleSort("last_seen")} className="inline-flex items-center gap-1">
                          Last Seen <ArrowUpDown size={12} />
                        </button>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {items.map((item) => (
                      <tr key={item.domain}>
                        <td className="max-w-xs truncate py-3 pr-4 text-slate-200" title={item.domain}>
                          {item.domain}
                        </td>
                        <td className="py-3 pr-4 font-semibold text-slate-200">{item.count}</td>
                        <td className="py-3 pr-4">
                          <Badge variant={RISK_VARIANT[item.risk_level]}>{item.risk_level}</Badge>
                        </td>
                        <td className="py-3 pr-4">
                          {item.is_blacklisted ? <Badge variant="danger">Blacklisted</Badge> : <span className="text-slate-600">—</span>}
                        </td>
                        <td className="whitespace-nowrap py-3 text-slate-400">{formatRelativeDate(item.last_seen)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-5 flex items-center justify-between border-t border-white/10 pt-4">
                <p className="text-xs text-slate-500">
                  Page {page} of {totalPages} · {total} domain{total === 1 ? "" : "s"}
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="btn-secondary px-3 py-1.5 disabled:opacity-30"
                  aria-label="Previous page"
                  >
                    <ChevronLeft size={16} aria-hidden="true" />
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                    className="btn-secondary px-3 py-1.5 disabled:opacity-30"
                  aria-label="Next page"
                  >
                    <ChevronRight size={16} aria-hidden="true" />
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
