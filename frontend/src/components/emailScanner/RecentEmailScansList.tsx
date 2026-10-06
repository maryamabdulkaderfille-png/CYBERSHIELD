import { Mail } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/common/Badge";
import { EmptyState } from "@/components/common/EmptyState";
import { formatRelativeDate, RISK_VARIANT } from "@/lib/risk";
import type { EmailScanHistoryItem } from "@/types/emailScan";

interface RecentEmailScansListProps {
  scans: EmailScanHistoryItem[];
  emptyDescription?: string;
}

export function RecentEmailScansList({ scans, emptyDescription }: RecentEmailScansListProps) {
  if (scans.length === 0) {
    return (
      <EmptyState
        icon={Mail}
        title="No emails scanned yet"
        description={emptyDescription ?? "Scan an email to see it show up here."}
      />
    );
  }

  return (
    <ul className="divide-y divide-white/5">
      {scans.map((scan) => (
        <li key={scan.id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-slate-200">
              {scan.subject || "(no subject)"}
            </p>
            <p className="truncate text-xs text-slate-500">
              {scan.sender_email || "Unknown sender"} · {formatRelativeDate(scan.scan_date)}
            </p>
          </div>
          <span className="shrink-0 text-sm font-semibold text-slate-300">{scan.trust_score}</span>
          <Badge variant={RISK_VARIANT[scan.risk_level]}>{scan.risk_level}</Badge>
        </li>
      ))}
    </ul>
  );
}

export function ViewAllEmailHistoryLink() {
  return (
    <Link to="/dashboard/history?tab=email" className="text-xs font-medium text-brand-cyan hover:underline">
      View all
    </Link>
  );
}
