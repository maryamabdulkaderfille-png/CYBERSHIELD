import type { RiskLevel, RuleResult } from "@/types/scan";

export interface EmailLinkFinding {
  url: string;
  trust_score: number;
  risk: RiskLevel;
}

export interface EmailAttachmentFinding {
  filename: string;
  is_dangerous: boolean;
  reason: string | null;
}

export interface EmailScanReport {
  id: number;
  sender_display_name: string | null;
  sender_email: string | null;
  subject: string | null;
  trust_score: number;
  risk: RiskLevel;
  reasons: string[];
  recommendations: string[];
  links: EmailLinkFinding[];
  attachments: EmailAttachmentFinding[];
  rules: RuleResult[];
  scan_date: string;
}

export interface EmailScanHistoryItem {
  id: number;
  sender_display_name: string | null;
  sender_email: string | null;
  subject: string | null;
  trust_score: number;
  risk_level: RiskLevel;
  link_count: number;
  attachment_count: number;
  scan_date: string;
}

export interface EmailScanHistoryResponse {
  items: EmailScanHistoryItem[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface EmailDashboardStats {
  total_emails_scanned: number;
  safe_count: number;
  low_risk_count: number;
  suspicious_count: number;
  dangerous_count: number;
  average_trust_score: number | null;
  recent_scans: EmailScanHistoryItem[];
}
