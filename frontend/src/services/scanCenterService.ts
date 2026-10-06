import { api } from "@/lib/api";
import type {
  DateRangeKey,
  ScannerType,
  UnifiedScanListResponse,
  UnifiedScanStats,
  UnifiedScanStatsRange,
  UnifiedScanStatsTrend,
} from "@/types/unifiedScan";

export interface UnifiedScanParams {
  page?: number;
  per_page?: number;
  scanner_type?: ScannerType;
  risk_level?: string;
  search?: string;
  trust_score_min?: number;
  trust_score_max?: number;
  date_from?: string;
  date_to?: string;
  sort_by?: "scan_date" | "trust_score";
  sort_dir?: "asc" | "desc";
}

export async function getUnifiedScans(params: UnifiedScanParams = {}): Promise<UnifiedScanListResponse> {
  const { data } = await api.get<UnifiedScanListResponse>("/scans", { params });
  return data;
}

export async function getUnifiedStats(): Promise<UnifiedScanStats> {
  const { data } = await api.get<UnifiedScanStats>("/scans/stats");
  return data;
}

export async function getUnifiedStatsRange(range: DateRangeKey): Promise<UnifiedScanStatsRange> {
  const { data } = await api.get<UnifiedScanStatsRange>("/scans/stats/range", { params: { range } });
  return data;
}

export async function getUnifiedStatsTrend(): Promise<UnifiedScanStatsTrend> {
  const { data } = await api.get<UnifiedScanStatsTrend>("/scans/stats/trend");
  return data;
}

export async function deleteScan(scannerType: ScannerType, id: number): Promise<void> {
  await api.delete(`/scans/${scannerType}/${id}`);
}

export async function bulkDeleteScans(
  items: { scanner_type: ScannerType; id: number }[]
): Promise<number> {
  const { data } = await api.post<{ deleted_count: number }>("/scans/bulk-delete", { items });
  return data.deleted_count;
}
