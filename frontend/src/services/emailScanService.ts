import { api } from "@/lib/api";
import type {
  EmailDashboardStats,
  EmailScanHistoryResponse,
  EmailScanReport,
} from "@/types/emailScan";
import type { RiskLevel } from "@/types/scan";

export async function scanEmailText(emailText: string): Promise<EmailScanReport> {
  const formData = new FormData();
  formData.append("email_text", emailText);
  const { data } = await api.post<EmailScanReport>("/email/scan", formData);
  return data;
}

export async function scanEmailFile(file: File): Promise<EmailScanReport> {
  const formData = new FormData();
  formData.append("email_file", file);
  const { data } = await api.post<EmailScanReport>("/email/scan", formData);
  return data;
}

export interface EmailScanHistoryParams {
  page?: number;
  per_page?: number;
  search?: string;
  risk_level?: RiskLevel;
}

export async function getEmailScanHistory(
  params: EmailScanHistoryParams = {}
): Promise<EmailScanHistoryResponse> {
  const { data } = await api.get<EmailScanHistoryResponse>("/email/history", { params });
  return data;
}

export async function getEmailScanDetail(id: number): Promise<EmailScanReport> {
  const { data } = await api.get<EmailScanReport>(`/email/history/${id}`);
  return data;
}

export async function getEmailDashboardStats(): Promise<EmailDashboardStats> {
  const { data } = await api.get<EmailDashboardStats>("/email/stats");
  return data;
}
