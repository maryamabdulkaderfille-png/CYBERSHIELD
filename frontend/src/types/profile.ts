import type { UnifiedScanItem } from "@/types/unifiedScan";

export interface ProfileStats {
  total_scans: number;
  safe_scans: number;
  dangerous_scans: number;
  reports_generated: number;
  url_scans: number;
  email_scans: number;
  qr_scans: number;
  security_score: number | null;
  recent_activity: UnifiedScanItem[];
}

export interface ExtendedProfileFields {
  phone?: string;
  country?: string;
  bio?: string;
  avatar_url?: string;
}
