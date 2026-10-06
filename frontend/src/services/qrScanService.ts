import { api } from "@/lib/api";
import type { QRDashboardStats, QRScanHistoryResponse, QRScanReport } from "@/types/qrScan";
import type { RiskLevel } from "@/types/scan";

export async function scanQrImage(file: File): Promise<QRScanReport> {
  const formData = new FormData();
  formData.append("qr_image", file);
  const { data } = await api.post<QRScanReport>("/qr/scan", formData);
  return data;
}

export interface QrScanHistoryParams {
  page?: number;
  per_page?: number;
  search?: string;
  risk_level?: RiskLevel;
}

export async function getQrScanHistory(params: QrScanHistoryParams = {}): Promise<QRScanHistoryResponse> {
  const { data } = await api.get<QRScanHistoryResponse>("/qr/history", { params });
  return data;
}

export async function getQrScanDetail(id: number): Promise<QRScanReport> {
  const { data } = await api.get<QRScanReport>(`/qr/history/${id}`);
  return data;
}

export async function getQrDashboardStats(): Promise<QRDashboardStats> {
  const { data } = await api.get<QRDashboardStats>("/qr/stats");
  return data;
}
