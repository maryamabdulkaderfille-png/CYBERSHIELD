export type NotificationType =
  | "high_risk_url"
  | "dangerous_email"
  | "qr_threat"
  | "report_generated"
  | "security_recommendation"
  // Phase 9 — Active Protection
  | "website_blocked"
  | "website_unblocked"
  | "extension_blocked_access"
  | "protection_mode_changed"
  | "community_threat_alert"
  | "weekly_summary";

export interface Notification {
  id: number;
  type: NotificationType;
  title: string;
  message: string;
  scanner_type: "url" | "email" | "qr" | null;
  scan_id: number | null;
  is_read: boolean;
  created_at: string;
}

export interface NotificationListResponse {
  items: Notification[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
  unread_count: number;
}
