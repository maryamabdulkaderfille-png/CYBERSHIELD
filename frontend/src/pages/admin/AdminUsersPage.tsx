import { ChevronLeft, ChevronRight, Search, Users } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/common/Badge";
import { EmptyState } from "@/components/common/EmptyState";
import { extractErrorMessage } from "@/lib/errors";
import * as adminService from "@/services/adminService";
import type { User, UserStatus } from "@/types/auth";

const PER_PAGE = 20;
const STATUS_FILTERS: (UserStatus | "")[] = ["", "active", "suspended", "removed"];
const STATUS_VARIANT: Record<UserStatus, "safe" | "warning" | "danger"> = {
  active: "safe",
  suspended: "warning",
  removed: "danger",
};

export function AdminUsersPage() {
  const [items, setItems] = useState<User[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<UserStatus | "">("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    adminService
      .listUsers({
        page,
        per_page: PER_PAGE,
        search: search || undefined,
        role: roleFilter || undefined,
        status: statusFilter || undefined,
      })
      .then((response) => {
        if (cancelled) return;
        setItems(response.items);
        setTotalPages(response.total_pages);
        setTotal(response.total);
      })
      .catch((err) => {
        if (!cancelled) setError(extractErrorMessage(err, "Could not load users."));
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [page, search, roleFilter, statusFilter]);

  const handleSearchSubmit = (event: FormEvent) => {
    event.preventDefault();
    setPage(1);
    setSearch(searchInput.trim());
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-50">User Management</h1>
        <p className="mt-1 text-sm text-slate-400">Search, filter, and manage every CyberShield account.</p>
      </div>

      <div className="glass-card flex flex-col gap-4 p-6">
        <form onSubmit={handleSearchSubmit} className="relative flex-1">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search by name, username, or email…"
            className="input-field pl-10"
          />
        </form>
        <div className="flex flex-wrap gap-2">
          {["", "user", "admin"].map((role) => (
            <button
              key={role || "all"}
              onClick={() => {
                setRoleFilter(role);
                setPage(1);
              }}
              className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                roleFilter === role
                  ? "border-brand-cyan/50 bg-brand-cyan/10 text-brand-cyan"
                  : "border-white/10 bg-white/[0.03] text-slate-400 hover:text-slate-200"
              }`}
            >
              {role ? role[0].toUpperCase() + role.slice(1) : "All roles"}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          {STATUS_FILTERS.map((status) => (
            <button
              key={status || "all"}
              onClick={() => {
                setStatusFilter(status);
                setPage(1);
              }}
              className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                statusFilter === status
                  ? "border-brand-cyan/50 bg-brand-cyan/10 text-brand-cyan"
                  : "border-white/10 bg-white/[0.03] text-slate-400 hover:text-slate-200"
              }`}
            >
              {status ? status[0].toUpperCase() + status.slice(1) : "All statuses"}
            </button>
          ))}
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
          <EmptyState icon={Users} title="No users found" description="Try a different search term or filter." />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-500">
                    <th className="pb-3 pr-4 font-medium">Name</th>
                    <th className="pb-3 pr-4 font-medium">Email</th>
                    <th className="pb-3 pr-4 font-medium">Role</th>
                    <th className="pb-3 pr-4 font-medium">Status</th>
                    <th className="pb-3 font-medium">Joined</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {items.map((user) => (
                    <tr key={user.id}>
                      <td className="py-3 pr-4">
                        <Link
                          to={`/admin/users/${user.id}`}
                          className="font-medium text-slate-200 hover:text-brand-cyan"
                        >
                          {user.full_name}
                        </Link>
                        <p className="text-xs text-slate-500">@{user.username}</p>
                      </td>
                      <td className="py-3 pr-4 text-slate-300">{user.email}</td>
                      <td className="py-3 pr-4">
                        <Badge variant={user.role === "admin" ? "danger" : "neutral"}>{user.role}</Badge>
                      </td>
                      <td className="py-3 pr-4">
                        <Badge variant={STATUS_VARIANT[user.status]}>
                          {user.status[0].toUpperCase() + user.status.slice(1)}
                        </Badge>
                      </td>
                      <td className="whitespace-nowrap py-3 text-slate-400">
                        {user.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-5 flex items-center justify-between border-t border-white/10 pt-4">
              <p className="text-xs text-slate-500">
                Page {page} of {totalPages} · {total} user{total === 1 ? "" : "s"}
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
