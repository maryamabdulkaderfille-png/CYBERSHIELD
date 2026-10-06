import type { User } from "@/types/auth";
import type { ProfileStats } from "@/types/profile";
import type { RiskLevel } from "@/types/scan";
import type { Session } from "@/types/settings";
import type { ThreatIntelligenceSummary } from "@/types/threatIntel";
import type { UnifiedScanItem } from "@/types/unifiedScan";

export interface AdminUserListResponse {
  items: User[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface AdminUserDetail {
  user: User;
  stats: ProfileStats;
  sessions: Session[];
}

export interface AdminScanItem extends UnifiedScanItem {
  user_id: string;
  username: string;
  source: "web" | "extension";
}

export interface AdminScanListResponse {
  items: AdminScanItem[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface BlacklistEntry {
  id: number;
  domain: string;
  reason: string;
  added_by_user_id: string | null;
  created_at: string;
  enabled: boolean;
}

export interface BlacklistListResponse {
  items: BlacklistEntry[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export type RuleCategory = "url" | "email";

export interface DetectionRule {
  id: number;
  key: string;
  category: RuleCategory;
  label: string;
  description: string | null;
  severity: "info" | "low" | "medium" | "high" | "critical";
  enabled: boolean;
  version: number;
  updated_at: string;
}

export type AuditAction =
  | "login"
  | "logout"
  | "profile_update"
  | "settings_update"
  | "admin_action"
  | "blacklist_update"
  | "rule_change"
  | "extension_event"
  | "report_generated"
  | "scan_deleted";

export interface AuditLogEntry {
  id: number;
  user_id: string | null;
  action: AuditAction;
  status: "success" | "failure";
  ip_address: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogListResponse {
  items: AuditLogEntry[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface SystemOverview {
  users: {
    total: number;
    active: number;
    inactive: number;
    verified: number;
    admins: number;
  };
  scans: {
    total_scans: number;
    safe_count: number;
    low_risk_count: number;
    suspicious_count: number;
    dangerous_count: number;
    by_scanner_type: { url: number; email: number; qr: number };
    average_trust_score: number | null;
    recent_scans: UnifiedScanItem[];
    latest_threats: UnifiedScanItem[];
    top_risks: UnifiedScanItem[];
  };
  extension_activity: { scans_recorded: number };
  notifications_sent: number;
  recent_logins: AuditLogEntry[];
  system_health: SystemHealth;
}

export interface AdminStats {
  overview: SystemOverview;
  threat_intelligence: ThreatIntelligenceSummary;
  active_users: { count: number; window_minutes: number };
}

export type RestrictableFeature = "url" | "email" | "qr" | "reports";

export interface UserRestrictionItem {
  id: number;
  feature: RestrictableFeature;
  restricted_by_user_id: string | null;
  restricted_at: string;
}

export interface SystemHealth {
  request_metrics: {
    total_requests: number;
    average_response_time_ms: number | null;
    error_rate_percent: number | null;
    requests_last_5_min: number;
  };
  database: { status: "healthy" | "unhealthy"; message: string };
  memory: { available: false; message: string };
  uptime_seconds: number;
}

// Re-exported for pages that only need a subset of the shared risk vocabulary.
export type { RiskLevel };
