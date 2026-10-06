import { Ban, Plus, Search, Trash2 } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";

import { Badge } from "@/components/common/Badge";
import { EmptyState } from "@/components/common/EmptyState";
import { useToast } from "@/context/ToastContext";
import { extractErrorMessage } from "@/lib/errors";
import { formatRelativeDate } from "@/lib/risk";
import * as adminService from "@/services/adminService";
import type { BlacklistEntry } from "@/types/admin";

const PER_PAGE = 20;

export function AdminBlacklistPage() {
  const { showToast } = useToast();
  const [items, setItems] = useState<BlacklistEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearchInput] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshNonce, setRefreshNonce] = useState(0);

  const [newDomain, setNewDomain] = useState("");
  const [newReason, setNewReason] = useState("");
  const [isAdding, setIsAdding] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  const refresh = () => setRefreshNonce((n) => n + 1);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    adminService
      .listBlacklist({ page: 1, per_page: PER_PAGE, search: search || undefined })
      .then((response) => {
        if (cancelled) return;
        setItems(response.items);
        setTotal(response.total);
      })
      .catch((err) => {
        if (!cancelled) setError(extractErrorMessage(err, "Could not load the blacklist."));
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [search, refreshNonce]);

  const handleAdd = async (event: FormEvent) => {
    event.preventDefault();
    setAddError(null);
    setIsAdding(true);
    try {
      await adminService.addBlacklistEntry(newDomain.trim(), newReason.trim() || undefined);
      setNewDomain("");
      setNewReason("");
      showToast("Domain added to blacklist.", "success");
      refresh();
    } catch (err) {
      setAddError(extractErrorMessage(err, "Could not add this domain."));
    } finally {
      setIsAdding(false);
    }
  };

  const handleToggle = async (entry: BlacklistEntry) => {
    try {
      if (entry.enabled) {
        await adminService.disableBlacklistEntry(entry.id);
      } else {
        await adminService.enableBlacklistEntry(entry.id);
      }
      refresh();
    } catch (err) {
      showToast(extractErrorMessage(err, "Could not update this entry."), "error");
    }
  };

  const handleRemove = async (entry: BlacklistEntry) => {
    try {
      await adminService.removeBlacklistEntry(entry.id);
      showToast("Blacklist entry removed.", "success");
      refresh();
    } catch (err) {
      showToast(extractErrorMessage(err, "Could not remove this entry."), "error");
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-50">Blacklist Management</h1>
        <p className="mt-1 text-sm text-slate-400">
          Domains here are flagged Dangerous by the URL Scanner's blacklist check.
        </p>
      </div>

      <div className="glass-card p-6">
        <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
          <Plus size={16} className="text-slate-400" />
          Add domain
        </h2>
        <form onSubmit={handleAdd} className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label className="mb-1.5 block text-sm font-medium text-slate-300">Domain</label>
            <input
              type="text"
              required
              value={newDomain}
              onChange={(e) => setNewDomain(e.target.value)}
              placeholder="evil-phish.example"
              className="input-field"
            />
          </div>
          <div className="flex-1">
            <label className="mb-1.5 block text-sm font-medium text-slate-300">Reason</label>
            <input
              type="text"
              value={newReason}
              onChange={(e) => setNewReason(e.target.value)}
              placeholder="Reported phishing domain"
              className="input-field"
            />
          </div>
          <button type="submit" disabled={isAdding} className="btn-primary px-5 py-2.5">
            <Plus size={16} />
            {isAdding ? "Adding…" : "Add"}
          </button>
        </form>
        {addError && <p className="mt-2 text-sm text-danger">{addError}</p>}
      </div>

      <div className="glass-card p-4">
        <div className="relative">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search blacklisted domains…"
            className="input-field pl-10"
          />
        </div>
      </div>

      <div className="glass-card p-6">
        {error ? (
          <p className="text-sm text-danger">{error}</p>
        ) : isLoading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded-lg bg-white/[0.03]" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <EmptyState icon={Ban} title="No blacklisted domains" description="Add a domain above to get started." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-500">
                  <th className="pb-3 pr-4 font-medium">Domain</th>
                  <th className="pb-3 pr-4 font-medium">Reason</th>
                  <th className="pb-3 pr-4 font-medium">Status</th>
                  <th className="pb-3 pr-4 font-medium">Added</th>
                  <th className="pb-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {items.map((entry) => (
                  <tr key={entry.id}>
                    <td className="py-3 pr-4 font-medium text-slate-200">{entry.domain}</td>
                    <td className="max-w-xs truncate py-3 pr-4 text-slate-400" title={entry.reason}>
                      {entry.reason}
                    </td>
                    <td className="py-3 pr-4">
                      <Badge variant={entry.enabled ? "danger" : "neutral"}>
                        {entry.enabled ? "Enabled" : "Disabled"}
                      </Badge>
                    </td>
                    <td className="whitespace-nowrap py-3 pr-4 text-slate-400">
                      {formatRelativeDate(entry.created_at)}
                    </td>
                    <td className="py-3">
                      <div className="flex gap-3">
                        <button
                          onClick={() => handleToggle(entry)}
                          className="text-xs font-medium text-brand-cyan hover:underline"
                        >
                          {entry.enabled ? "Disable" : "Enable"}
                        </button>
                        <button
                          onClick={() => handleRemove(entry)}
                          className="flex items-center gap-1 text-xs font-medium text-danger hover:underline"
                        >
                          <Trash2 size={12} />
                          Remove
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-4 text-xs text-slate-500">{total} total entries</p>
          </div>
        )}
      </div>
    </div>
  );
}
