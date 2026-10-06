export type RiskLevel = "Safe" | "Low Risk" | "Suspicious" | "Dangerous";

export type RuleSeverity = "info" | "low" | "medium" | "high" | "critical";

export interface RuleResult {
  rule: string;
  label: string;
  triggered: boolean;
  impact: number;
  severity: RuleSeverity;
  message: string;
  detail: string | null;
}

export interface ScanReport {
  id: number;
  url: string;
  trust_score: number;
  risk: RiskLevel;
  reasons: string[];
  recommendations: string[];
  rules: RuleResult[];
  scan_date: string;
}

export interface ScanHistoryItem {
  id: number;
  url: string;
  trust_score: number;
  risk_level: RiskLevel;
  scan_date: string;
}

export interface ScanHistoryResponse {
  items: ScanHistoryItem[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface DashboardStats {
  total_scans: number;
  safe_count: number;
  low_risk_count: number;
  suspicious_count: number;
  dangerous_count: number;
  average_trust_score: number | null;
  recent_scans: ScanHistoryItem[];
}
