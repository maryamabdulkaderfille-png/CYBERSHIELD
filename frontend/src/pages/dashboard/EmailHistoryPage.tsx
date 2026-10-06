import { ChevronLeft, ChevronRight, Mail, Search } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";

import { Badge } from "@/components/common/Badge";
import { EmptyState } from "@/components/common/EmptyState";
import { extractErrorMessage } from "@/lib/errors";
import { formatRelativeDate, RISK_VARIANT } from "@/lib/risk";
import * as emailScanService from "@/services/emailScanService";
import type { EmailScanHistoryItem } from "@/types/emailScan";
import type { RiskLevel } from "@/types/scan";

const PER_PAGE = 10;
const RISK_FILTERS: (RiskLevel | "All")[] = ["All", "Safe", "Low Risk", "Suspicious", "Dangerous"];

export function EmailHistoryPage() {
  const [items, setItems] = useState<EmailScanHistoryItem[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [riskFilter, setRiskFilter] = useState<RiskLevel | "All">("All");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    emailScanService
      .getEmailScanHistory({
        page,
        per_page: PER_PAGE,
        search: search || undefined,
        risk_level: riskFilter === "All" ? undefined : riskFilter,
      })
      .then((response) => {
        if (cancelled) return;
        setItems(response.items);
        setTotalPages(response.total_pages);
        setTotal(response.total);
      })
      .catch((err) => {
        if (!cancelled) setError(extractErrorMessage(err, "Could not load email scan history."));
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [page, search, riskFilter]);

  const handleSearchSubmit = (event: FormEvent) => {
    event.preventDefault();
    setPage(1);
    setSearch(searchInput.trim());
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="glass-card p-6">
        <div className="flex flex-col gap-3 sm:flex-row">
          <form onSubmit={handleSearchSubmit} className="relative flex-1">
            <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search by sender or subject…"
              className="input-field pl-10"
            />
          </form>

          <div className="flex flex-wrap gap-2">
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
      </div>

      <div className="glass-card p-6">
        {error ? (
          <p className="text-sm text-danger">{error}</p>
        ) : isLoading ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : items.length === 0 ? (
          <EmptyState
            icon={Mail}
            title="No emails found"
            description="Try a different search term or filter, or analyze a new email from the Email Scanner page."
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-500">
                    <th className="pb-3 pr-4 font-medium">Sender</th>
                    <th className="pb-3 pr-4 font-medium">Subject</th>
                    <th className="pb-3 pr-4 font-medium">Date</th>
                    <th className="pb-3 pr-4 font-medium">Trust Score</th>
                    <th className="pb-3 font-medium">Risk Level</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {items.map((item) => (
                    <tr key={item.id}>
                      <td className="max-w-[12rem] truncate py-3 pr-4 text-slate-200" title={item.sender_email ?? ""}>
                        {item.sender_email || "Unknown"}
                      </td>
                      <td className="max-w-xs truncate py-3 pr-4 text-slate-300" title={item.subject ?? ""}>
                        {item.subject || "(no subject)"}
                      </td>
                      <td className="whitespace-nowrap py-3 pr-4 text-slate-400">
                        {formatRelativeDate(item.scan_date)}
                      </td>
                      <td className="py-3 pr-4 font-semibold text-slate-200">{item.trust_score}</td>
                      <td className="py-3">
                        <Badge variant={RISK_VARIANT[item.risk_level]}>{item.risk_level}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-5 flex items-center justify-between border-t border-white/10 pt-4">
              <p className="text-xs text-slate-500">
                Page {page} of {totalPages} · {total} total email{total === 1 ? "" : "s"}
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
  );
}
