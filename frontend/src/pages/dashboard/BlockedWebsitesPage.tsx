import { Ban, ChevronLeft, ChevronRight, Download, RotateCcw, Search, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/common/Badge";
import { EmptyState } from "@/components/common/EmptyState";
import { useToast } from "@/context/ToastContext";
import { extractErrorMessage } from "@/lib/errors";
import { formatRelativeDate, RISK_VARIANT } from "@/lib/risk";
import * as protectionService from "@/services/protectionService";
import type { BlockedWebsite } from "@/types/protection";
import type { RiskLevel } from "@/types/scan";

const PER_PAGE = 20;
const RISK_FILTERS: (RiskLevel | "")[] = ["", "Dangerous", "Suspicious", "Low Risk", "Safe"];

export function BlockedWebsitesPage() {
  const { showToast } = useToast();
  const [items, setItems] = useState<BlockedWebsite[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState<RiskLevel | "">("");
  const [showActive, setShowActive] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshNonce, setRefreshNonce] = useState(0);

  const refresh = () => setRefreshNonce((n) => n + 1);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    protectionService
      .listBlockedWebsites({
        page,
        per_page: PER_PAGE,
        search: search || undefined,
        risk_level: riskFilter || undefined,
        is_active: showActive,
        sort_by: "blocked_at",
        sort_dir: "desc",
      })
      .then((response) => {
        if (cancelled) return;
        setItems(response.items);
        setTotalPages(response.total_pages);
        setTotal(response.total);
      })
      .catch((err) => {
        if (!cancelled) setError(extractErrorMessage(err, "Could not load your block list."));
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [page, search, riskFilter, showActive, refreshNonce]);

  const handleUnblock = async (entry: BlockedWebsite) => {
    try {
      await protectionService.unblockWebsite(entry.id);
      showToast(`${entry.domain} removed from your block list.`, "success");
      refresh();
    } catch (err) {
      showToast(extractErrorMessage(err, "Could not remove this entry."), "error");
    }
  };

  const handleRestore = async (entry: BlockedWebsite) => {
    try {
      await protectionService.restoreWebsite(entry.id);
      showToast(`${entry.domain} restored to your block list.`, "success");
      refresh();
    } catch (err) {
      showToast(extractErrorMessage(err, "Could not restore this entry."), "error");
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-50">Blocked Websites</h1>
          <p className="mt-1 text-sm text-slate-400">
            Your Personal Block List — the browser extension enforces these automatically.
          </p>
        </div>
        <div className="flex gap-2">
          <a href={protectionService.getExportUrl("json")} className="btn-secondary px-4 py-2 text-xs" download>
            <Download size={14} aria-hidden="true" />
            Export JSON
          </a>
          <a href={protectionService.getExportUrl("csv")} className="btn-secondary px-4 py-2 text-xs" download>
            <Download size={14} aria-hidden="true" />
            Export CSV
          </a>
        </div>
      </div>

      <div className="glass-card flex flex-wrap items-center gap-3 p-4">
        <div className="relative flex-1" style={{ minWidth: 220 }}>
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Search blocked domains…"
            className="input-field pl-10"
          />
        </div>

        <div className="flex flex-wrap gap-2">
          {RISK_FILTERS.map((risk) => (
            <button
              key={risk || "all"}
              onClick={() => {
                setRiskFilter(risk);
                setPage(1);
              }}
              className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                riskFilter === risk
                  ? "border-brand-cyan/50 bg-brand-cyan/10 text-brand-cyan"
                  : "border-white/10 bg-white/[0.03] text-slate-400 hover:text-slate-200"
              }`}
            >
              {risk || "All risks"}
            </button>
          ))}
        </div>

        <div className="ml-auto inline-flex rounded-xl border border-white/10 bg-white/[0.03] p-1">
          <button
            onClick={() => {
              setShowActive(true);
              setPage(1);
            }}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              showActive ? "bg-brand-cyan/15 text-brand-cyan" : "text-slate-400"
            }`}
          >
            Active
          </button>
          <button
            onClick={() => {
              setShowActive(false);
              setPage(1);
            }}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              !showActive ? "bg-brand-cyan/15 text-brand-cyan" : "text-slate-400"
            }`}
          >
            Removed
          </button>
        </div>
      </div>

      <div className="glass-card p-6">
        {error ? (
          <p className="text-sm text-danger">{error}</p>
        ) : isLoading ? (
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded-lg bg-white/[0.03]" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            icon={Ban}
            title={showActive ? "No blocked websites" : "Nothing removed"}
            description={
              showActive
                ? "Block a Dangerous site from a URL scan result to see it here."
                : "Websites you remove from your block list will show up here, restorable at any time."
            }
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-500">
                    <th className="pb-3 pr-4 font-medium">Domain</th>
                    <th className="pb-3 pr-4 font-medium">Risk</th>
                    <th className="pb-3 pr-4 font-medium">Trust Score</th>
                    <th className="pb-3 pr-4 font-medium">{showActive ? "Blocked" : "Removed"}</th>
                    <th className="pb-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {items.map((entry) => (
                    <tr key={entry.id}>
                      <td className="max-w-xs truncate py-3 pr-4 font-medium text-slate-200" title={entry.reasons.join(", ")}>
                        {entry.domain}
                      </td>
                      <td className="py-3 pr-4">
                        <Badge variant={RISK_VARIANT[entry.risk_level]}>{entry.risk_level}</Badge>
                      </td>
                      <td className="py-3 pr-4 text-slate-400">{entry.trust_score}/100</td>
                      <td className="whitespace-nowrap py-3 pr-4 text-slate-400">
                        {formatRelativeDate(showActive ? entry.blocked_at : entry.unblocked_at ?? entry.blocked_at)}
                      </td>
                      <td className="py-3">
                        {showActive ? (
                          <button
                            onClick={() => handleUnblock(entry)}
                            className="flex items-center gap-1 text-xs font-medium text-danger hover:underline"
                          >
                            <Trash2 size={12} aria-hidden="true" />
                            Remove
                          </button>
                        ) : (
                          <button
                            onClick={() => handleRestore(entry)}
                            className="flex items-center gap-1 text-xs font-medium text-brand-cyan hover:underline"
                          >
                            <RotateCcw size={12} aria-hidden="true" />
                            Restore
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-5 flex items-center justify-between border-t border-white/10 pt-4">
              <p className="text-xs text-slate-500">
                Page {page} of {totalPages} · {total} entries
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  aria-label="Previous page"
                  className="btn-secondary px-3 py-1.5 disabled:opacity-30"
                >
                  <ChevronLeft size={16} aria-hidden="true" />
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  aria-label="Next page"
                  className="btn-secondary px-3 py-1.5 disabled:opacity-30"
                >
                  <ChevronRight size={16} aria-hidden="true" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
