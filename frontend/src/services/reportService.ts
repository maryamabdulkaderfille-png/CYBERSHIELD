import { api } from "@/lib/api";
import type { Report } from "@/types/report";
import type { ScannerType } from "@/types/unifiedScan";

export async function getReport(scannerType: ScannerType, scanId: number): Promise<Report> {
  const { data } = await api.get<Report>(`/reports/${scannerType}/${scanId}`);
  return data;
}

export async function exportReportPdf(scannerType: ScannerType, scanId: number): Promise<void> {
  const response = await api.post(
    `/reports/${scannerType}/${scanId}/export`,
    { format: "pdf" },
    { responseType: "blob" }
  );
  const blob = new Blob([response.data], { type: "application/pdf" });
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = downloadUrl;
  link.setAttribute("download", `cybershield-report-${scannerType}-${scanId}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(downloadUrl);
}
