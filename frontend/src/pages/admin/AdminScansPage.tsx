import {
  ChevronLeft,
  ChevronRight,
  Download,
  LayoutGrid,
  Mail,
  QrCode,
  Search,
  ShieldCheck,
  Trash2,
} from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { Badge } from "@/components/common/Badge";
import { EmptyState } from "@/components/common/EmptyState";
import { useToast } from "@/context/ToastContext";
import { extractErrorMessage } from "@/lib/errors";
import { formatRelativeDate, RISK_VARIANT } from "@/lib/risk";
import * as adminService from "@/services/adminService";
import type { AdminScanItem } from "@/types/admin";
import type { RiskLevel } from "@/types/scan";

const PER_PAGE = 15;
const RISK_FILTERS: (RiskLevel | "All")[] = ["All", "Safe", "Low Risk", "Suspicious", "Dangerous"];
const TYPE_FILTERS: { value: "url" | "email" | "qr" | "All"; label: string; icon: typeof ShieldCheck }[] = [
  { value: "All", label: "All Types", icon: LayoutGrid },
  { value: "url", label: "URL", icon: ShieldCheck },
  { value: "email", label: "Email", icon: Mail },
  { value: "qr", label: "QR", icon: QrCode },
];
const SOURCE_FILTERS: { value: "web" | "extension" | "All"; label: string }[] = [
  { value: "All", label: "All Sources" },
  { value: "web", label: "Web" },
  { value: "extension", label: "Extension" },
];

export function AdminScansPage() {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [items, setItems] = useState<AdminScanItem[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [riskFilter, setRiskFilter] = useState<RiskLevel | "All">("All");
  const [typeFilter, setTypeFilter] = useState<"url" | "email" | "qr" | "All">("All");
  const [sourceFilter, setSourceFilter] = useState<"web" | "extension" | "All">("All");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshNonce, setRefreshNonce] = useState(0);

  const rowKey = (item: AdminScanItem) => `${item.scanner_type}:${item.id}`;

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    adminService
      .listAllScans({
        page,
        per_page: PER_PAGE,
        search: search || undefined,
        risk_level: riskFilter === "All" ? undefined : riskFilter,
        scanner_type: typeFilter === "All" ? undefined : typeFilter,
        source: sourceFilter === "All" ? undefined : sourceFilter,
      })
      .then((response) => {
        if (cancelled) return;
        setItems(response.items);
        setTotalPages(response.total_pages);
        setTotal(response.total);
      })
      .catch((err) => {
        if (!cancelled) setError(extractErrorMessage(err, "Could not load scans."));
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [page, search, riskFilter, typeFilter, sourceFilter, refreshNonce]);

  const handleSearchSubmit = (event: FormEvent) => {
    event.preventDefault();
    setPage(1);
    setSearch(searchInput.trim());
  };

  const toggleSelected = (key: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const refresh = () => setRefreshNonce((n) => n + 1);

  const handleDeleteOne = async (item: AdminScanItem) => {
    try {
      await adminService.deleteScan(item.scanner_type, item.id);
      showToast("Scan deleted.", "success");
      refresh();
    } catch (err) {
      showToast(extractErrorMessage(err, "Could not delete this scan."), "error");
    }
  };

  const handleBulkDelete = async () => {
    const toDelete = items
      .filter((item) => selected.has(rowKey(item)))
      .map((item) => ({ scanner_type: item.scanner_type, id: item.id }));
    if (toDelete.length === 0) return;

    try {
      const count = await adminService.bulkDeleteScans(toDelete);
      showToast(`${count} scan(s) deleted.`, "success");
      setSelected(new Set());
      refresh();
    } catch (err) {
      showToast(extractErrorMessage(err, "Could not delete the selected scans."), "error");
    }
  };

  const handleExport = async () => {
    try {
      await adminService.exportScans();
    } catch (err) {
      showToast(extractErrorMessage(err, "Scan export is coming in a future update."), "info");
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-50">Scan Management</h1>
          <p className="mt-1 text-sm text-slate-400">Every scan across every user — URL, Email, QR, and browser extension.</p>
        </div>
        <button onClick={handleExport} className="btn-secondary">
          <Download size={16} />
          Export
        </button>
      </div>

      <div className="glass-card flex flex-col gap-4 p-6">
        <form onSubmit={handleSearchSubmit} className="relative flex-1">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search across all scans…"
            className="input-field pl-10"
          />
        </form>

        <div className="flex flex-wrap items-center gap-2">
          {TYPE_FILTERS.map((filter) => (
            <button
              key={filter.value}
              onClick={() => {
                setTypeFilter(filter.value);
                setPage(1);
              }}
              className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                typeFilter === filter.value
                  ? "border-brand-cyan/50 bg-brand-cyan/10 text-brand-cyan"
                  : "border-white/10 bg-white/[0.03] text-slate-400 hover:text-slate-200"
              }`}
            >
              <filter.icon size={13} />
              {filter.label}
            </button>
          ))}
          <span className="mx-1 h-4 w-px bg-white/10" />
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
          <span className="mx-1 h-4 w-px bg-white/10" />
          {SOURCE_FILTERS.map((filter) => (
            <button
              key={filter.value}
              onClick={() => {
                setSourceFilter(filter.value);
                setPage(1);
              }}
              className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                sourceFilter === filter.value
                  ? "border-brand-cyan/50 bg-brand-cyan/10 text-brand-cyan"
                  : "border-white/10 bg-white/[0.03] text-slate-400 hover:text-slate-200"
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      {selected.size > 0 && (
        <div className="glass-card flex items-center justify-between p-4">
          <p className="text-sm text-slate-300">{selected.size} selected</p>
          <button onClick={handleBulkDelete} className="btn-secondary border-danger/30 px-4 py-2 text-xs text-danger">
            <Trash2 size={14} />
            Delete Selected
          </button>
        </div>
      )}

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
          <EmptyState icon={LayoutGrid} title="No scans found" description="Try a different search term or filter." />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-500">
                    <th className="w-8 pb-3 pr-2">
                      <input
                        type="checkbox"
                        checked={selected.size > 0 && selected.size === items.length}
                        onChange={() =>
                          setSelected(selected.size === items.length ? new Set() : new Set(items.map(rowKey)))
                        }
                        className="h-4 w-4 rounded border-white/20 bg-white/5"
                      />
                    </th>
                    <th className="pb-3 pr-4 font-medium">Type</th>
                    <th className="pb-3 pr-4 font-medium">User</th>
                    <th className="pb-3 pr-4 font-medium">Target</th>
                    <th className="pb-3 pr-4 font-medium">Source</th>
                    <th className="pb-3 pr-4 font-medium">Date</th>
                    <th className="pb-3 pr-4 font-medium">Trust Score</th>
                    <th className="pb-3 pr-4 font-medium">Risk</th>
                    <th className="pb-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {items.map((item) => (
                    <tr key={rowKey(item)}>
                      <td className="py-3 pr-2">
                        <input
                          type="checkbox"
                          checked={selected.has(rowKey(item))}
                          onChange={() => toggleSelected(rowKey(item))}
                          className="h-4 w-4 rounded border-white/20 bg-white/5"
                        />
                      </td>
                      <td className="py-3 pr-4">
                        <Badge variant="brand">{item.scanner_type.toUpperCase()}</Badge>
                      </td>
                      <td className="py-3 pr-4 text-slate-300">{item.username}</td>
                      <td className="max-w-xs truncate py-3 pr-4 text-slate-200" title={item.target}>
                        {item.target}
                      </td>
                      <td className="py-3 pr-4">
                        <Badge variant={item.source === "extension" ? "brand" : "neutral"}>{item.source}</Badge>
                      </td>
                      <td className="whitespace-nowrap py-3 pr-4 text-slate-400">
                        {formatRelativeDate(item.scan_date)}
                      </td>
                      <td className="py-3 pr-4 font-semibold text-slate-200">{item.trust_score}</td>
                      <td className="py-3 pr-4">
                        <Badge variant={RISK_VARIANT[item.risk_level]}>{item.risk_level}</Badge>
                      </td>
                      <td className="py-3">
                        <div className="flex gap-2">
                          <button
                            onClick={() => navigate(`/dashboard/reports/${item.scanner_type}/${item.id}`)}
                            className="text-xs font-medium text-brand-cyan hover:underline"
                          >
                            View
                          </button>
                          <button
                            onClick={() => handleDeleteOne(item)}
                            className="text-xs font-medium text-danger hover:underline"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-5 flex items-center justify-between border-t border-white/10 pt-4">
              <p className="text-xs text-slate-500">
                Page {page} of {totalPages} · {total} total scan{total === 1 ? "" : "s"}
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
