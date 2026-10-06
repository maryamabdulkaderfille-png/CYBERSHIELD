import type { ProtectionMode } from "@/types/protection";

export type Theme = "dark" | "light" | "system";
export type ProfileVisibility = "private" | "public";

export interface UserSettings {
  theme: Theme;
  language: string;
  timezone: string;
  notify_high_risk_url: boolean;
  notify_dangerous_email: boolean;
  notify_qr_threat: boolean;
  notify_weekly_summary: boolean;
  profile_visibility: ProfileVisibility;
  protection_mode: ProtectionMode;
}

export interface Session {
  id: number;
  user_agent: string | null;
  ip_address: string | null;
  created_at: string;
  last_seen_at: string;
  is_revoked: boolean;
  is_current: boolean;
}
