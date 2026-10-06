import { api } from "@/lib/api";
import type { DashboardStats, RiskLevel, ScanHistoryResponse, ScanReport } from "@/types/scan";

export async function scanUrl(url: string): Promise<ScanReport> {
  const { data } = await api.post<ScanReport>("/url/scan", { url });
  return data;
}

export interface ScanHistoryParams {
  page?: number;
  per_page?: number;
  search?: string;
  risk_level?: RiskLevel;
}

export async function getScanHistory(params: ScanHistoryParams = {}): Promise<ScanHistoryResponse> {
  const { data } = await api.get<ScanHistoryResponse>("/url/history", { params });
  return data;
}

export async function getScanDetail(id: number): Promise<ScanReport> {
  const { data } = await api.get<ScanReport>(`/url/history/${id}`);
  return data;
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await api.get<DashboardStats>("/url/stats");
  return data;
}
