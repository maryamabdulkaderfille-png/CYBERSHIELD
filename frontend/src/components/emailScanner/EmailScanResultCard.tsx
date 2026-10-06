import { motion } from "framer-motion";
import { ChevronDown, ListChecks, Paperclip, ShieldAlert } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/common/Badge";
import { TrustScoreGauge } from "@/components/scanner/TrustScoreGauge";
import { RISK_VARIANT } from "@/lib/risk";
import type { EmailScanReport } from "@/types/emailScan";

const SEVERITY_DOT: Record<string, string> = {
  info: "bg-slate-600",
  low: "bg-brand-cyan",
  medium: "bg-warning",
  high: "bg-danger",
  critical: "bg-danger",
};

export function EmailScanResultCard({ report }: { report: EmailScanReport }) {
  const [showAllRules, setShowAllRules] = useState(false);

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
      <div className="flex flex-col items-center gap-6 border-b border-white/10 pb-6 sm:flex-row sm:items-start">
        <TrustScoreGauge score={report.trust_score} risk={report.risk} />

        <div className="flex-1 space-y-2 text-center sm:text-left">
          <div>
            <p className="text-sm text-slate-500">From</p>
            <p className="break-all font-medium text-slate-100">
              {report.sender_display_name ? `${report.sender_display_name} ` : ""}
              {report.sender_email ? (
                <span className="text-slate-400">&lt;{report.sender_email}&gt;</span>
              ) : (
                <span className="text-danger">No sender found</span>
              )}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Subject</p>
            <p className="break-words font-medium text-slate-100">{report.subject || "(no subject)"}</p>
          </div>
          <div className="flex justify-center sm:justify-start">
            <Badge variant={RISK_VARIANT[report.risk]}>Risk Level: {report.risk}</Badge>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 pt-6 md:grid-cols-2">
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-200">
            <ShieldAlert size={16} className="text-slate-400" />
            Reasons
          </h3>
          {report.reasons.length === 0 ? (
            <p className="text-sm text-slate-500">No risk indicators were detected for this email.</p>
          ) : (
            <ul className="space-y-2">
              {report.reasons.map((reason, index) => (
                <li key={index} className="text-sm leading-relaxed text-slate-300">
                  {reason}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-200">
            <ListChecks size={16} className="text-slate-400" />
            Recommendations
          </h3>
          <ul className="space-y-2">
            {report.recommendations.map((rec, index) => (
              <li key={index} className="text-sm leading-relaxed text-slate-300">
                • {rec}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {report.links.length > 0 && (
        <div className="border-t border-white/10 pt-6">
          <h3 className="mb-3 text-sm font-semibold text-slate-200">Links found ({report.links.length})</h3>
          <ul className="space-y-2">
            {report.links.map((link) => (
              <li
                key={link.url}
                className="flex items-center justify-between gap-3 rounded-xl border border-white/5 bg-white/[0.02] px-3 py-2.5"
              >
                <span className="min-w-0 truncate text-sm text-slate-300">{link.url}</span>
                <div className="flex shrink-0 items-center gap-2">
                  <span className="text-xs text-slate-500">{link.trust_score}</span>
                  <Badge variant={RISK_VARIANT[link.risk]}>{link.risk}</Badge>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {report.attachments.length > 0 && (
        <div className="border-t border-white/10 pt-6">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-200">
            <Paperclip size={16} className="text-slate-400" />
            Attachments ({report.attachments.length})
          </h3>
          <ul className="space-y-2">
            {report.attachments.map((attachment) => (
              <li
                key={attachment.filename}
                className="flex items-center justify-between gap-3 rounded-xl border border-white/5 bg-white/[0.02] px-3 py-2.5"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm text-slate-300">{attachment.filename}</p>
                  {attachment.reason && <p className="text-xs text-danger">{attachment.reason}</p>}
                </div>
                <Badge variant={attachment.is_dangerous ? "danger" : "safe"}>
                  {attachment.is_dangerous ? "Dangerous" : "Safe"}
                </Badge>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-6 border-t border-white/10 pt-4">
        <button
          onClick={() => setShowAllRules((prev) => !prev)}
          className="flex w-full items-center justify-between text-sm font-medium text-slate-400 hover:text-slate-200"
        >
          Full rule-by-rule breakdown ({report.rules.length} checks)
          <ChevronDown size={16} className={`transition-transform ${showAllRules ? "rotate-180" : ""}`} />
        </button>

        {showAllRules && (
          <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
            {report.rules.map((rule) => (
              <div
                key={rule.rule}
                className="flex items-start gap-2.5 rounded-xl border border-white/5 bg-white/[0.02] px-3 py-2.5"
              >
                <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${SEVERITY_DOT[rule.severity]}`} />
                <div>
                  <p className="text-xs font-semibold text-slate-300">{rule.label}</p>
                  <p className="text-xs text-slate-500">{rule.message}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
