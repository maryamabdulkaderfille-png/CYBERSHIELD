import type { RiskLevel, RuleResult } from "@/types/scan";
import type { ScannerType } from "@/types/unifiedScan";

export interface Report {
  report_id: string;
  scanner_type: ScannerType;
  scan_id: number;
  generated_at: string;
  scan_date: string;
  user: { id: string; username: string; full_name: string; email: string };
  target: string;
  trust_score: number;
  risk_level: RiskLevel;
  summary: string;
  findings: { reasons: string[]; rules: RuleResult[] };
  recommendations: string[];
  raw: Record<string, unknown>;
}
