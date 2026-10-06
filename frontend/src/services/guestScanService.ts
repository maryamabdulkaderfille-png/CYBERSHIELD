/**
 * Guest / Quick Scan — calls the public, unauthenticated backend endpoints
 * (`/guest/url/scan`, `/guest/email/scan`, `/guest/qr/scan`). These reuse
 * the exact same detection engines as the authenticated scanners (see
 * backend `app/routes/v1/guest.py`); the only difference is nothing is
 * persisted, so the response has no `id`/history. The existing
 * `ScanReport`/`EmailScanReport`/`QRScanReport` types and result-card
 * components are reused as-is by synthesizing a placeholder `id: 0` here
 * (none of those components actually read `.id`), rather than introducing
 * parallel "guest" types.
 */
import { api } from "@/lib/api";
import type { EmailScanReport } from "@/types/emailScan";
import type { QRScanReport } from "@/types/qrScan";
import type { ScanReport } from "@/types/scan";

export async function guestScanUrl(url: string): Promise<ScanReport> {
  const { data } = await api.post<Omit<ScanReport, "id">>("/guest/url/scan", { url });
  return { id: 0, ...data };
}

export async function guestScanEmailText(emailText: string): Promise<EmailScanReport> {
  const formData = new FormData();
  formData.append("email_text", emailText);
  const { data } = await api.post<Omit<EmailScanReport, "id">>("/guest/email/scan", formData);
  return { id: 0, ...data };
}

export async function guestScanEmailFile(file: File): Promise<EmailScanReport> {
  const formData = new FormData();
  formData.append("email_file", file);
  const { data } = await api.post<Omit<EmailScanReport, "id">>("/guest/email/scan", formData);
  return { id: 0, ...data };
}

export async function guestScanQrImage(file: File): Promise<QRScanReport> {
  const formData = new FormData();
  formData.append("qr_image", file);
  const { data } = await api.post<Omit<QRScanReport, "id">>("/guest/qr/scan", formData);
  return { id: 0, ...data };
}
