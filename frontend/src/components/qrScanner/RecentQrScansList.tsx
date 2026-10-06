import { QrCode } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/common/Badge";
import { EmptyState } from "@/components/common/EmptyState";
import { formatRelativeDate, RISK_VARIANT } from "@/lib/risk";
import type { QRScanHistoryItem } from "@/types/qrScan";

interface RecentQrScansListProps {
  scans: QRScanHistoryItem[];
  emptyDescription?: string;
}

export function RecentQrScansList({ scans, emptyDescription }: RecentQrScansListProps) {
  if (scans.length === 0) {
    return (
      <EmptyState
        icon={QrCode}
        title="No QR codes scanned yet"
        description={emptyDescription ?? "Scan a QR code to see it show up here."}
      />
    );
  }

  return (
    <ul className="divide-y divide-white/5">
      {scans.map((scan) => (
        <li key={scan.id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-slate-200">{scan.raw_content}</p>
            <p className="text-xs capitalize text-slate-500">
              {scan.content_type.replace("_", " ")} · {formatRelativeDate(scan.scan_date)}
            </p>
          </div>
          <span className="shrink-0 text-sm font-semibold text-slate-300">{scan.trust_score}</span>
          <Badge variant={RISK_VARIANT[scan.risk_level]}>{scan.risk_level}</Badge>
        </li>
      ))}
    </ul>
  );
}

export function ViewAllQrHistoryLink() {
  return (
    <Link to="/dashboard/scan-center?type=qr" className="text-xs font-medium text-brand-cyan hover:underline">
      View all
    </Link>
  );
}
