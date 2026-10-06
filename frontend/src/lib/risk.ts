import type { RiskLevel, RuleSeverity } from "@/types/scan";

type RiskVariant = "safe" | "brand" | "warning" | "danger";

export const RISK_VARIANT: Record<RiskLevel, RiskVariant> = {
  Safe: "safe",
  "Low Risk": "brand",
  Suspicious: "warning",
  Dangerous: "danger",
};

export const RISK_TEXT_COLOR: Record<RiskLevel, string> = {
  Safe: "text-safe",
  "Low Risk": "text-brand-cyan",
  Suspicious: "text-warning",
  Dangerous: "text-danger",
};

export const RISK_RING_COLOR: Record<RiskLevel, string> = {
  Safe: "#22c55e",
  "Low Risk": "#22d3ee",
  Suspicious: "#eab308",
  Dangerous: "#ef4444",
};

export const RISK_EMOJI: Record<RiskLevel, string> = {
  Safe: "🟢",
  "Low Risk": "🟢",
  Suspicious: "🟡",
  Dangerous: "🔴",
};

export const SEVERITY_VARIANT: Record<RuleSeverity, RiskVariant | "neutral"> = {
  info: "neutral",
  low: "brand",
  medium: "warning",
  high: "danger",
  critical: "danger",
};

export function formatRelativeDate(isoDate: string): string {
  const date = new Date(isoDate);
  const diffMs = Date.now() - date.getTime();
  const diffMinutes = Math.round(diffMs / 60000);

  if (diffMinutes < 1) return "just now";
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.round(diffHours / 24);
  if (diffDays < 30) return `${diffDays}d ago`;
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}
