import { AlertTriangle, Ban, Check, ClipboardCopy, Flag, ShieldOff, Sparkles, Users, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/common/Badge";
import { useToast } from "@/context/ToastContext";
import { extractErrorMessage } from "@/lib/errors";
import * as protectionService from "@/services/protectionService";
import type { CommunityIntel, SecurityExplanation } from "@/types/protection";
import type { ScanReport } from "@/types/scan";

interface BlockWebsitePanelProps {
  report: ScanReport;
}

function hostOf(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return url;
  }
}

/** Shown only under an existing Dangerous or Suspicious scan result — never
 * replaces or alters ScanResultCard, which is rendered unchanged right above
 * this. Safe and Low Risk results never render this panel. */
export function BlockWebsitePanel({ report }: BlockWebsitePanelProps) {
  const { showToast } = useToast();
  const domain = useMemo(() => hostOf(report.url), [report.url]);
  const isDangerous = report.risk === "Dangerous";

  const [isDismissed, setIsDismissed] = useState(false);
  const [isBlocked, setIsBlocked] = useState(false);
  const [isBlocking, setIsBlocking] = useState(false);
  const [isReported, setIsReported] = useState(false);
  const [isReporting, setIsReporting] = useState(false);
  const [explanation, setExplanation] = useState<SecurityExplanation | null>(null);
  const [community, setCommunity] = useState<CommunityIntel | null>(null);

  useEffect(() => {
    setIsDismissed(false);
    setIsBlocked(false);
    setIsReported(false);
    setExplanation(null);
    setCommunity(null);

    protectionService
      .explainResult({ risk: report.risk, trust_score: report.trust_score, reasons: report.reasons, rules: report.rules })
      .then(setExplanation)
      .catch(() => {});

    protectionService
      .getCommunityIntel([domain])
      .then((map) => setCommunity(map[domain] ?? null))
      .catch(() => {});
  }, [report.id, domain, report.risk, report.trust_score, report.reasons, report.rules]);

  if ((report.risk !== "Dangerous" && report.risk !== "Suspicious") || isDismissed) return null;

  const handleBlock = async () => {
    setIsBlocking(true);
    try {
      const entry = await protectionService.blockWebsite({
        target: report.url,
        trust_score: report.trust_score,
        risk_level: report.risk,
        reasons: report.reasons,
        scanner_type: "url",
        scan_id: report.id,
      });
      setIsBlocked(true);
      showToast(`${entry.domain} has been added to your Block List.`, "success");
    } catch (err) {
      showToast(extractErrorMessage(err, "Could not block this website."), "error");
    } finally {
      setIsBlocking(false);
    }
  };

  const handleReport = async () => {
    setIsReporting(true);
    try {
      await protectionService.reportWebsite(report.url, report.reasons);
      setIsReported(true);
      showToast("Reported for admin review — thank you.", "success");
    } catch (err) {
      showToast(extractErrorMessage(err, "Could not report this website."), "error");
    } finally {
      setIsReporting(false);
    }
  };

  const handleCopyReport = async () => {
    const lines = [
      "CyberShield Scan Report",
      `Website: ${report.url}`,
      `Trust Score: ${report.trust_score}/100`,
      `Risk Level: ${report.risk}`,
      "",
      "Reasons:",
      ...report.reasons.map((reason) => `- ${reason}`),
      "",
      `Scanned: ${report.scan_date}`,
    ];
    try {
      await navigator.clipboard.writeText(lines.join("\n"));
      showToast("Report copied to clipboard.", "success");
    } catch {
      showToast("Could not copy to clipboard.", "error");
    }
  };

  const iconWrapClass = isDangerous ? "bg-danger/10 text-danger" : "bg-warning/10 text-warning";
  const accentTextClass = isDangerous ? "text-danger" : "text-warning";

  return (
    <div className={`glass-card p-6 ${isDangerous ? "border-danger/30" : "border-warning/30"}`}>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${iconWrapClass}`}>
            <AlertTriangle size={22} aria-hidden="true" />
          </span>
          <div>
            <h2 className="text-base font-semibold text-slate-100">
              {isDangerous ? "Dangerous Website Detected" : "Suspicious Website Detected"}
            </h2>
            <p className="text-sm text-slate-400">
              Trust Score: <span className={`font-semibold ${accentTextClass}`}>{report.trust_score}/100</span>
            </p>
          </div>
        </div>
        {community && community.blocked_by_users > 0 && (
          <div className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-slate-300">
            <Users size={13} className="text-brand-cyan" aria-hidden="true" />
            Blocked by {community.blocked_by_users} CyberShield user{community.blocked_by_users === 1 ? "" : "s"}
            <Badge variant="brand">{community.confidence_percent}% confidence</Badge>
          </div>
        )}
      </div>

      {report.reasons.length > 0 && (
        <div className="mt-4">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Reasons</p>
          <ul className="space-y-1.5">
            {report.reasons.map((reason) => (
              <li key={reason} className="flex items-start gap-2 text-sm text-slate-300">
                <Check size={15} className={`mt-0.5 shrink-0 ${accentTextClass}`} aria-hidden="true" />
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {explanation && (
        <div className="mt-4 rounded-xl border border-white/10 bg-white/[0.02] p-4">
          <p className="mb-1.5 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <Sparkles size={13} className="text-brand-cyan" aria-hidden="true" />
            {isDangerous ? "Why is this dangerous?" : "Why is this suspicious?"}
          </p>
          <p className="text-sm text-slate-300">{explanation.summary}</p>
          <p className="mt-2 text-sm text-slate-400">
            <span className="font-medium text-slate-300">Recommendation: </span>
            {explanation.recommendation}
          </p>
        </div>
      )}

      <div className="mt-5 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={handleBlock}
          disabled={isBlocking || isBlocked}
          className={`btn-primary px-5 ${isDangerous ? "bg-danger from-danger to-danger" : "bg-warning from-warning to-warning"}`}
        >
          <Ban size={16} aria-hidden="true" />
          {isBlocked ? "Blocked" : isBlocking ? "Blocking…" : "Block Website"}
        </button>
        <button type="button" onClick={handleReport} disabled={isReporting || isReported} className="btn-secondary px-5">
          <Flag size={16} aria-hidden="true" />
          {isReported ? "Reported" : isReporting ? "Reporting…" : "Report Website"}
        </button>
        <button type="button" onClick={handleCopyReport} className="btn-secondary px-5">
          <ClipboardCopy size={16} aria-hidden="true" />
          Copy Report
        </button>
        <button type="button" onClick={() => setIsDismissed(true)} className="btn-secondary px-5 text-slate-400">
          <X size={16} aria-hidden="true" />
          Continue Anyway
        </button>
      </div>

      {isBlocked && (
        <p className="mt-3 flex items-center gap-1.5 text-xs text-slate-500">
          <ShieldOff size={13} aria-hidden="true" />
          The browser extension will now block future visits to {domain} automatically.
        </p>
      )}
    </div>
  );
}
