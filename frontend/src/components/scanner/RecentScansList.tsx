import { Link } from "react-router-dom";

import { Badge } from "@/components/common/Badge";
import { EmptyState } from "@/components/common/EmptyState";
import { formatRelativeDate, RISK_VARIANT } from "@/lib/risk";
import { truncateMiddle } from "@/lib/url";
import type { ScanHistoryItem } from "@/types/scan";
import { Activity } from "lucide-react";

interface RecentScansListProps {
  scans: ScanHistoryItem[];
  emptyDescription?: string;
}

export function RecentScansList({ scans, emptyDescription }: RecentScansListProps) {
  if (scans.length === 0) {
    return (
      <EmptyState
        icon={Activity}
        title="No scans yet"
        description={emptyDescription ?? "Scan a URL to see it show up here."}
      />
    );
  }

  return (
    <ul className="divide-y divide-white/5">
      {scans.map((scan) => (
        <li key={scan.id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-slate-200" title={scan.url}>
              {truncateMiddle(scan.url)}
            </p>
            <p className="text-xs text-slate-500">{formatRelativeDate(scan.scan_date)}</p>
          </div>
          <span className="shrink-0 text-sm font-semibold text-slate-300">{scan.trust_score}</span>
          <Badge variant={RISK_VARIANT[scan.risk_level]}>{scan.risk_level}</Badge>
        </li>
      ))}
    </ul>
  );
}

export function ViewAllHistoryLink() {
  return (
    <Link to="/dashboard/history" className="text-xs font-medium text-brand-cyan hover:underline">
      View all
    </Link>
  );
}
