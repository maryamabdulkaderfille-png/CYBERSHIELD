import {
  AlertTriangle,
  Ban,
  BarChart3,
  FileText,
  Mail,
  QrCode,
  ShieldAlert,
  ShieldCheck,
  ShieldOff,
  Users,
  type LucideIcon,
} from "lucide-react";

import type { NotificationType } from "@/types/notification";

export const NOTIFICATION_ICON: Record<NotificationType, LucideIcon> = {
  high_risk_url: AlertTriangle,
  dangerous_email: Mail,
  qr_threat: QrCode,
  report_generated: FileText,
  security_recommendation: ShieldAlert,
  // Phase 9 — Active Protection
  website_blocked: Ban,
  website_unblocked: ShieldCheck,
  extension_blocked_access: ShieldOff,
  protection_mode_changed: ShieldAlert,
  community_threat_alert: Users,
  weekly_summary: BarChart3,
};

export const NOTIFICATION_COLOR: Record<NotificationType, string> = {
  high_risk_url: "text-danger bg-danger/10",
  dangerous_email: "text-danger bg-danger/10",
  qr_threat: "text-warning bg-warning/10",
  report_generated: "text-brand-cyan bg-brand-cyan/10",
  security_recommendation: "text-brand-cyan bg-brand-cyan/10",
  // Phase 9 — Active Protection
  website_blocked: "text-danger bg-danger/10",
  website_unblocked: "text-safe bg-safe/10",
  extension_blocked_access: "text-danger bg-danger/10",
  protection_mode_changed: "text-brand-cyan bg-brand-cyan/10",
  community_threat_alert: "text-warning bg-warning/10",
  weekly_summary: "text-brand-cyan bg-brand-cyan/10",
};
