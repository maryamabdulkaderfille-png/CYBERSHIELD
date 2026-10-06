import type { RiskLevel } from "@/types/scan";

export type ProtectionMode = "warn_only" | "ask_before_blocking" | "auto_block_dangerous" | "auto_block_dangerous_suspicious";

export interface BlockedWebsite {
  id: number;
  domain: string;
  trust_score: number;
  risk_level: RiskLevel;
  reasons: string[];
  scanner_type: string;
  scan_id: number | null;
  is_active: boolean;
  blocked_at: string;
  unblocked_at: string | null;
}

export interface BlockedWebsiteListResponse {
  items: BlockedWebsite[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface ProtectionStats {
  blocked_today: number;
  blocked_this_week: number;
  total_blocked_domains: number;
  recent_blocked: BlockedWebsite[];
}

export interface CommunityIntel {
  domain: string;
  blocked_by_users: number;
  confidence_percent: number;
  first_seen: string | null;
  recent_activity: string | null;
}

export interface SecurityExplanation {
  risk: RiskLevel;
  trust_score: number;
  summary: string;
  points: string[];
  recommendation: string;
}
