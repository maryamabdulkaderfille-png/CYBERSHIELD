import { api } from "@/lib/api";
import type { ThreatDomainListResponse, ThreatIntelligenceSummary } from "@/types/threatIntel";

export async function getThreatIntelligenceSummary(): Promise<ThreatIntelligenceSummary> {
  const { data } = await api.get<ThreatIntelligenceSummary>("/threats");
  return data;
}

export interface ThreatDomainParams {
  page?: number;
  per_page?: number;
  search?: string;
  risk_level?: string;
  sort_by?: "count" | "last_seen" | "domain";
  sort_dir?: "asc" | "desc";
}

export async function getThreatDomains(params: ThreatDomainParams = {}): Promise<ThreatDomainListResponse> {
  const { data } = await api.get<ThreatDomainListResponse>("/threats/domains", { params });
  return data;
}

/** Always rejects with a 501 today — see the backend's threats_bp export
 * route for the prepared-but-unimplemented export interface. */
export async function exportThreatIntelligence(): Promise<void> {
  await api.get("/threats/export");
}
