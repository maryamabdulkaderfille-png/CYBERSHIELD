import type { RiskLevel } from "@/types/scan";
import type { DailyCount, DomainCount, KeywordCount } from "@/types/dashboardIntel";

export interface KnownPhishingDomain {
  domain: string;
  reason: string;
  added_at: string;
}

export interface BrandCount {
  brand: string;
  count: number;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface BlockedDomain {
  domain: string;
  reason: string | null;
  blocked_at: string;
}

export interface ThreatStatistics {
  total_scans: number;
  safe_count: number;
  low_risk_count: number;
  suspicious_count: number;
  dangerous_count: number;
  blacklisted_domains: number;
}

export interface SeverityDistribution {
  safe: number;
  low_risk: number;
  suspicious: number;
  dangerous: number;
}

export interface ThreatFeedArchitecture {
  provider: string;
  live_feed_enabled: boolean;
  message: string;
}

export interface ThreatIntelligenceSummary {
  known_phishing_domains: KnownPhishingDomain[];
  suspicious_domains: DomainRow[];
  recently_blocked_domains: BlockedDomain[];
  top_targeted_brands: BrandCount[];
  most_common_keywords: KeywordCount[];
  attack_categories: CategoryCount[];
  threat_statistics: ThreatStatistics;
  severity_distribution: SeverityDistribution;
  detection_trends: DailyCount[];
  blacklist_overview: { total: number; entries: KnownPhishingDomain[] };
  threat_feed_architecture: ThreatFeedArchitecture;
}

export interface DomainRow {
  domain: string;
  count: number;
  risk_level: RiskLevel;
  last_seen: string;
  is_blacklisted: boolean;
}

export interface ThreatDomainListResponse {
  items: DomainRow[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

// Re-export for convenience so pages only need one import for shared shapes.
export type { DomainCount };
