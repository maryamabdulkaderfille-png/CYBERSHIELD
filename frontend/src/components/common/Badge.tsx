import type { ReactNode } from "react";

type BadgeVariant = "safe" | "warning" | "danger" | "neutral" | "brand";

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  safe: "bg-safe/10 text-safe border-safe/30",
  warning: "bg-warning/10 text-warning border-warning/30",
  danger: "bg-danger/10 text-danger border-danger/30",
  neutral: "bg-white/5 text-slate-400 border-white/10",
  brand: "bg-brand-cyan/10 text-brand-cyan border-brand-cyan/30",
};

export function Badge({ variant = "neutral", children }: { variant?: BadgeVariant; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${VARIANT_CLASSES[variant]}`}
    >
      {children}
    </span>
  );
}
