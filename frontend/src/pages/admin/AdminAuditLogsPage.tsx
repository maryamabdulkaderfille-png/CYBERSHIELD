import { ChevronLeft, ChevronRight, FileClock } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/common/Badge";
import { EmptyState } from "@/components/common/EmptyState";
import { extractErrorMessage } from "@/lib/errors";
import { formatRelativeDate } from "@/lib/risk";
import * as adminService from "@/services/adminService";
import type { AuditAction, AuditLogEntry } from "@/types/admin";

const PER_PAGE = 25;
const ACTIONS: (AuditAction | "")[] = [
  "",
  "login",
  "logout",
  "profile_update",
  "settings_update",
  "admin_action",
  "blacklist_update",
  "rule_change",
  "extension_event",
  "report_generated",
  "scan_deleted",
];

export function AdminAuditLogsPage() {
  const [items, setItems] = useState<AuditLogEntry[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [actionFilter, setActionFilter] = useState<AuditAction | "">("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    adminService
      .listAuditLogs({
        page,
        per_page: PER_PAGE,
        action: actionFilter || undefined,
        date_from: dateFrom ? `${dateFrom}T00:00:00Z` : undefined,
        date_to: dateTo ? `${dateTo}T23:59:59Z` : undefined,
      })
      .then((response) => {
        if (cancelled) return;
        setItems(response.items);
        setTotalPages(response.total_pages);
        setTotal(response.total);
      })
      .catch((err) => {
        if (!cancelled) setError(extractErrorMessage(err, "Could not load audit logs."));
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [page, actionFilter, dateFrom, dateTo]);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold text-slate-50">
          <FileClock size={22} />
          Audit Logs
        </h1>
        <p className="mt-1 text-sm text-slate-400">Security-relevant activity across the platform.</p>
      </div>

      <div className="glass-card flex flex-wrap gap-2 p-4">
        {ACTIONS.map((action) => (
          <button
            key={action || "all"}
            onClick={() => {
              setActionFilter(action);
              setPage(1);
            }}
            className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
              actionFilter === action
                ? "border-brand-cyan/50 bg-brand-cyan/10 text-brand-cyan"
                : "border-white/10 bg-white/[0.03] text-slate-400 hover:text-slate-200"
            }`}
          >
            {action ? action.replace(/_/g, " ") : "All actions"}
          </button>
        ))}
      </div>

      <div className="glass-card flex flex-wrap items-end gap-4 p-4">
        <label className="flex flex-col gap-1.5 text-xs font-medium text-slate-400">
          From
          <input
            type="date"
            value={dateFrom}
            max={dateTo || undefined}
            onChange={(e) => {
              setDateFrom(e.target.value);
              setPage(1);
            }}
            className="input-field py-1.5"
          />
        </label>
        <label className="flex flex-col gap-1.5 text-xs font-medium text-slate-400">
          To
          <input
            type="date"
            value={dateTo}
            min={dateFrom || undefined}
            onChange={(e) => {
              setDateTo(e.target.value);
              setPage(1);
            }}
            className="input-field py-1.5"
          />
        </label>
        {(dateFrom || dateTo) && (
          <button
            onClick={() => {
              setDateFrom("");
              setDateTo("");
              setPage(1);
            }}
            className="text-xs font-medium text-brand-cyan hover:underline"
          >
            Clear dates
          </button>
        )}
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
          <EmptyState icon={FileClock} title="No audit entries" description="Try a different filter." />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-500">
                    <th className="pb-3 pr-4 font-medium">Timestamp</th>
                    <th className="pb-3 pr-4 font-medium">User</th>
                    <th className="pb-3 pr-4 font-medium">Action</th>
                    <th className="pb-3 pr-4 font-medium">IP</th>
                    <th className="pb-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {items.map((log) => (
                    <tr key={log.id}>
                      <td className="whitespace-nowrap py-3 pr-4 text-slate-400">
                        {formatRelativeDate(log.created_at)}
                      </td>
                      <td className="py-3 pr-4 text-slate-300">
                        {(log.details?.email as string) ?? log.user_id ?? "—"}
                      </td>
                      <td className="py-3 pr-4">
                        <Badge variant="brand">{log.action.replace(/_/g, " ")}</Badge>
                      </td>
                      <td className="py-3 pr-4 text-slate-400">{log.ip_address ?? "—"}</td>
                      <td className="py-3">
                        <Badge variant={log.status === "success" ? "safe" : "danger"}>{log.status}</Badge>
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
