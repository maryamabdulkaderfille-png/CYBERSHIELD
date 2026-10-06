import type { RiskLevel, RuleResult } from "@/types/scan";

export type QRContentType =
  | "url"
  | "email"
  | "phone"
  | "sms"
  | "wifi"
  | "crypto"
  | "plain_text"
  | "unknown";

export interface QRScanReport {
  id: number;
  content_type: QRContentType;
  raw_content: string;
  parsed_fields: Record<string, unknown>;
  trust_score: number;
  risk: RiskLevel;
  reasons: string[];
  recommendations: string[];
  rules: RuleResult[];
  scan_date: string;
}

export interface QRScanHistoryItem {
  id: number;
  content_type: QRContentType;
  raw_content: string;
  trust_score: number;
  risk_level: RiskLevel;
  scan_date: string;
}

export interface QRScanHistoryResponse {
  items: QRScanHistoryItem[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface QRDashboardStats {
  total_qr_scanned: number;
  safe_count: number;
  low_risk_count: number;
  suspicious_count: number;
  dangerous_count: number;
  average_trust_score: number | null;
  recent_scans: QRScanHistoryItem[];
}
