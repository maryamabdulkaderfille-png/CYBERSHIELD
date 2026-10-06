import { api } from "@/lib/api";
import type { User, UserStatus } from "@/types/auth";
import type {
  AdminScanListResponse,
  AdminStats,
  AdminUserDetail,
  AdminUserListResponse,
  AuditLogListResponse,
  BlacklistEntry,
  BlacklistListResponse,
  DetectionRule,
  RestrictableFeature,
  RuleCategory,
  SystemHealth,
  SystemOverview,
  UserRestrictionItem,
} from "@/types/admin";

// --- Dashboard ---
export async function getSystemOverview(): Promise<SystemOverview> {
  const { data } = await api.get<SystemOverview>("/admin/dashboard");
  return data;
}

// --- Platform stats (System Overview + Threat Intelligence, admin-gated) ---
export async function getStats(): Promise<AdminStats> {
  const { data } = await api.get<AdminStats>("/admin/stats");
  return data;
}

// --- Users ---
export interface AdminUserParams {
  page?: number;
  per_page?: number;
  search?: string;
  role?: string;
  is_active?: boolean;
  status?: UserStatus;
}

export async function listUsers(params: AdminUserParams = {}): Promise<AdminUserListResponse> {
  const { data } = await api.get<AdminUserListResponse>("/admin/users", { params });
  return data;
}

export async function getUserDetail(userId: string): Promise<AdminUserDetail> {
  const { data } = await api.get<AdminUserDetail>(`/admin/users/${userId}`);
  return data;
}

export async function deactivateUser(userId: string): Promise<User> {
  const { data } = await api.post<{ user: User }>(`/admin/users/${userId}/deactivate`);
  return data.user;
}

export async function reactivateUser(userId: string): Promise<User> {
  const { data } = await api.post<{ user: User }>(`/admin/users/${userId}/reactivate`);
  return data.user;
}

/** Always rejects with a 501 today — prepared-but-unimplemented, same
 * pattern as PDF report export / data export. */
export async function resetUserPassword(userId: string): Promise<void> {
  await api.post(`/admin/users/${userId}/reset-password`);
}

export async function setUserStatus(userId: string, status: UserStatus): Promise<User> {
  const { data } = await api.patch<{ user: User }>(`/admin/users/${userId}/status`, { status });
  return data.user;
}

// --- Feature restrictions ---
export async function listUserRestrictions(userId: string): Promise<UserRestrictionItem[]> {
  const { data } = await api.get<{ items: UserRestrictionItem[] }>(`/admin/users/${userId}/restrictions`);
  return data.items;
}

export async function addUserRestriction(userId: string, feature: RestrictableFeature): Promise<UserRestrictionItem> {
  const { data } = await api.post<{ restriction: UserRestrictionItem }>(`/admin/users/${userId}/restrictions`, {
    feature,
  });
  return data.restriction;
}

export async function removeUserRestriction(userId: string, feature: RestrictableFeature): Promise<void> {
  await api.delete(`/admin/users/${userId}/restrictions/${feature}`);
}

// --- Scans ---
export interface AdminScanParams {
  page?: number;
  per_page?: number;
  scanner_type?: "url" | "email" | "qr";
  risk_level?: string;
  search?: string;
  source?: "web" | "extension";
  sort_by?: "scan_date" | "trust_score";
  sort_dir?: "asc" | "desc";
}

export async function listAllScans(params: AdminScanParams = {}): Promise<AdminScanListResponse> {
  const { data } = await api.get<AdminScanListResponse>("/admin/scans", { params });
  return data;
}

export async function deleteScan(scannerType: string, id: number): Promise<void> {
  await api.delete(`/admin/scans/${scannerType}/${id}`);
}

export async function bulkDeleteScans(items: { scanner_type: string; id: number }[]): Promise<number> {
  const { data } = await api.post<{ deleted_count: number }>("/admin/scans/bulk-delete", { items });
  return data.deleted_count;
}

export async function exportScans(): Promise<void> {
  await api.get("/admin/scans/export");
}

// --- Blacklist ---
export async function listBlacklist(params: { page?: number; per_page?: number; search?: string; enabled?: boolean } = {}): Promise<BlacklistListResponse> {
  const { data } = await api.get<BlacklistListResponse>("/admin/blacklist", { params });
  return data;
}

export async function addBlacklistEntry(domain: string, reason?: string): Promise<BlacklistEntry> {
  const { data } = await api.post<{ entry: BlacklistEntry }>("/admin/blacklist", { domain, reason });
  return data.entry;
}

export async function removeBlacklistEntry(id: number): Promise<void> {
  await api.delete(`/admin/blacklist/${id}`);
}

export async function enableBlacklistEntry(id: number): Promise<BlacklistEntry> {
  const { data } = await api.put<{ entry: BlacklistEntry }>(`/admin/blacklist/${id}/enable`);
  return data.entry;
}

export async function disableBlacklistEntry(id: number): Promise<BlacklistEntry> {
  const { data } = await api.put<{ entry: BlacklistEntry }>(`/admin/blacklist/${id}/disable`);
  return data.entry;
}

// --- Rules ---
export async function listRules(category?: RuleCategory): Promise<DetectionRule[]> {
  const { data } = await api.get<{ items: DetectionRule[] }>("/admin/rules", { params: { category } });
  return data.items;
}

export async function toggleRule(id: number, enabled: boolean): Promise<DetectionRule> {
  const { data } = await api.put<{ rule: DetectionRule }>(`/admin/rules/${id}`, { enabled });
  return data.rule;
}

// --- Audit logs ---
export interface AuditLogParams {
  page?: number;
  per_page?: number;
  action?: string;
  user_id?: string;
  status?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
}

export async function listAuditLogs(params: AuditLogParams = {}): Promise<AuditLogListResponse> {
  const { data } = await api.get<AuditLogListResponse>("/admin/audit-logs", { params });
  return data;
}

// --- System monitoring ---
export async function getSystemHealth(): Promise<SystemHealth> {
  const { data } = await api.get<SystemHealth>("/admin/system/health");
  return data;
}
