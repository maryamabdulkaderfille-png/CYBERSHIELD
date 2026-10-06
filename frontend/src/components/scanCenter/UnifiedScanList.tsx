import { Mail, QrCode, ShieldCheck, type LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/common/Badge";
import { EmptyState } from "@/components/common/EmptyState";
import { formatRelativeDate, RISK_VARIANT } from "@/lib/risk";
import { truncateMiddle } from "@/lib/url";
import type { UnifiedScanItem } from "@/types/unifiedScan";

const TYPE_ICON: Record<UnifiedScanItem["scanner_type"], LucideIcon> = {
  url: ShieldCheck,
  email: Mail,
  qr: QrCode,
};

interface UnifiedScanListProps {
  items: UnifiedScanItem[];
  emptyIcon: LucideIcon;
  emptyTitle: string;
  emptyDescription: string;
}

export function UnifiedScanList({ items, emptyIcon, emptyTitle, emptyDescription }: UnifiedScanListProps) {
  if (items.length === 0) {
    return <EmptyState icon={emptyIcon} title={emptyTitle} description={emptyDescription} />;
  }

  return (
    <ul className="divide-y divide-white/5">
      {items.map((item) => {
        const Icon = TYPE_ICON[item.scanner_type];
        return (
          <li key={`${item.scanner_type}:${item.id}`} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
            <Icon size={14} className="shrink-0 text-slate-500" />
            <Link
              to={`/dashboard/reports/${item.scanner_type}/${item.id}`}
              className="min-w-0 flex-1 truncate text-sm font-medium text-slate-200 hover:text-brand-cyan"
              title={item.target}
            >
              {truncateMiddle(item.target)}
            </Link>
            <p className="shrink-0 text-xs text-slate-500">{formatRelativeDate(item.scan_date)}</p>
            <span className="shrink-0 text-sm font-semibold text-slate-300">{item.trust_score}</span>
            <Badge variant={RISK_VARIANT[item.risk_level]}>{item.risk_level}</Badge>
          </li>
        );
      })}
    </ul>
  );
}
