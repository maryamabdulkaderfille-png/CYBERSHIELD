import { api } from "@/lib/api";
import type { RiskLevel, RuleResult } from "@/types/scan";
import type {
  BlockedWebsite,
  BlockedWebsiteListResponse,
  CommunityIntel,
  ProtectionStats,
  SecurityExplanation,
} from "@/types/protection";

export interface BlockWebsiteParams {
  target: string;
  trust_score: number;
  risk_level: RiskLevel;
  reasons: string[];
  scanner_type?: "url" | "email" | "qr";
  scan_id?: number | null;
}

export async function blockWebsite(params: BlockWebsiteParams): Promise<BlockedWebsite> {
  const { data } = await api.post<{ entry: BlockedWebsite }>("/protection/blocklist", params);
  return data.entry;
}

export interface BlockListParams {
  page?: number;
  per_page?: number;
  search?: string;
  risk_level?: RiskLevel;
  is_active?: boolean;
  sort_by?: "blocked_at" | "domain" | "trust_score";
  sort_dir?: "asc" | "desc";
}

export async function listBlockedWebsites(params: BlockListParams = {}): Promise<BlockedWebsiteListResponse> {
  const { data } = await api.get<BlockedWebsiteListResponse>("/protection/blocklist", { params });
  return data;
}

export async function unblockWebsite(id: number): Promise<BlockedWebsite> {
  const { data } = await api.delete<{ entry: BlockedWebsite }>(`/protection/blocklist/${id}`);
  return data.entry;
}

export async function restoreWebsite(id: number): Promise<BlockedWebsite> {
  const { data } = await api.post<{ entry: BlockedWebsite }>(`/protection/blocklist/${id}/restore`);
  return data.entry;
}

export function getExportUrl(format: "json" | "csv"): string {
  return `${api.defaults.baseURL}/protection/blocklist/export?format=${format}`;
}

export async function getProtectionStats(): Promise<ProtectionStats> {
  const { data } = await api.get<ProtectionStats>("/protection/stats");
  return data;
}

export async function getCommunityIntel(domains: string[]): Promise<Record<string, CommunityIntel>> {
  if (domains.length === 0) return {};
  const { data } = await api.get<{ items: Record<string, CommunityIntel> }>("/protection/community", {
    params: { domains: domains.join(",") },
  });
  return data.items;
}

export async function getTopCommunityThreats(): Promise<CommunityIntel[]> {
  const { data } = await api.get<{ items: CommunityIntel[] }>("/protection/community/top");
  return data.items;
}

export interface ExplainParams {
  risk: RiskLevel;
  trust_score: number;
  reasons: string[];
  rules: RuleResult[];
}

export async function explainResult(params: ExplainParams): Promise<SecurityExplanation> {
  const { data } = await api.post<SecurityExplanation>("/protection/explain", params);
  return data;
}

export async function reportWebsite(target: string, reasons: string[] = []): Promise<void> {
  await api.post("/protection/report", { target, reasons });
}
