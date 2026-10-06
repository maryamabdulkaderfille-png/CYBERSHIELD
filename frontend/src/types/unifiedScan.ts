import type { RiskLevel } from "@/types/scan";

export type ScannerType = "url" | "email" | "qr";

export interface UnifiedScanItem {
  scanner_type: ScannerType;
  id: number;
  target: string;
  trust_score: number;
  risk_level: RiskLevel;
  scan_date: string;
}

export interface UnifiedScanListResponse {
  items: UnifiedScanItem[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface UnifiedScanStats {
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
}

export type DateRangeKey = "today" | "7d" | "30d" | "all";

export interface UnifiedScanStatsRange {
  range: DateRangeKey;
  total_scans: number;
  safe_count: number;
  low_risk_count: number;
  suspicious_count: number;
  dangerous_count: number;
  by_scanner_type: { url: number; email: number; qr: number };
  average_trust_score: number | null;
}

export interface TrendCountPoint {
  date: string;
  count: number;
}

export interface TrendValuePoint {
  date: string;
  value: number | null;
}

export interface TrendCountMetric {
  current: number | null;
  previous: number | null;
  delta_pct: number | null;
  series: TrendCountPoint[];
}

export interface TrendValueMetric {
  current: number | null;
  previous: number | null;
  delta_pct: number | null;
  series: TrendValuePoint[];
}

export interface UnifiedScanStatsTrend {
  total_scans: TrendCountMetric;
  safe_count: TrendCountMetric;
  threats_count: TrendCountMetric;
  average_trust_score: TrendValueMetric;
}
