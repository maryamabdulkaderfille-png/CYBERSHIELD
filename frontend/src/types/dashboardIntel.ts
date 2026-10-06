import type { Notification } from "@/types/notification";
import type { UnifiedScanItem } from "@/types/unifiedScan";

export interface DailyCount {
  date: string;
  count: number;
}

export interface HeatmapRow {
  weekday: string;
  Safe: number;
  "Low Risk": number;
  Suspicious: number;
  Dangerous: number;
}

export interface DomainCount {
  domain: string;
  count: number;
}

export interface KeywordCount {
  keyword: string;
  count: number;
}

export interface DetectionAccuracyPlaceholder {
  available: false;
  message: string;
}

export interface DashboardIntelligence {
  overall_security_score: number | null;
  threat_trend: DailyCount[];
  recent_threat_timeline: UnifiedScanItem[];
  weekly_activity: DailyCount[];
  monthly_activity: DailyCount[];
  scan_distribution: { url: number; email: number; qr: number };
  risk_distribution: { safe: number; low_risk: number; suspicious: number; dangerous: number };
  most_dangerous_domains: DomainCount[];
  most_common_keywords: KeywordCount[];
  most_common_scanner: string | null;
  threat_heatmap: HeatmapRow[];
  average_scan_duration_ms: number | null;
  detection_accuracy: DetectionAccuracyPlaceholder;
  recent_notifications: Notification[];
  unread_notification_count: number;
}
