import {
  ArrowLeft,
  Download,
  FileText,
  ListChecks,
  Printer,
  Share2,
  ShieldAlert,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { Badge } from "@/components/common/Badge";
import { LoadingScreen } from "@/components/common/LoadingScreen";
import { useToast } from "@/context/ToastContext";
import { extractErrorMessage } from "@/lib/errors";
import { formatRelativeDate, RISK_VARIANT } from "@/lib/risk";
import * as reportService from "@/services/reportService";
import type { Report } from "@/types/report";
import type { ScannerType } from "@/types/unifiedScan";

type Tab = "overview" | "technical" | "indicators" | "recommendations";

const TABS: { value: Tab; label: string }[] = [
  { value: "overview", label: "Overview" },
  { value: "technical", label: "Technical Details" },
  { value: "indicators", label: "Detected Indicators" },
  { value: "recommendations", label: "Recommendations" },
];

export function ReportPage() {
  const { scannerType, scanId } = useParams<{ scannerType: ScannerType; scanId: string }>();
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [report, setReport] = useState<Report | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("overview");

  useEffect(() => {
    if (!scannerType || !scanId) return;
    setIsLoading(true);
    reportService
      .getReport(scannerType, Number(scanId))
      .then(setReport)
      .catch((err) => setError(extractErrorMessage(err, "Could not load this report.")))
      .finally(() => setIsLoading(false));
  }, [scannerType, scanId]);

  const handlePrint = () => window.print();

  const handleShare = async () => {
    const url = window.location.href;
    if (navigator.share) {
      try {
        await navigator.share({ title: "CyberShield Security Report", url });
        return;
      } catch {
        // user cancelled the native share sheet — fall through to clipboard
      }
    }
    if (navigator.clipboard) {
      try {
        await navigator.clipboard.writeText(url);
        showToast("Report link copied to clipboard.", "success");
        return;
      } catch {
        // fall through to error toast below
      }
    }
    showToast("Sharing isn't available in this browser context.", "error");
  };

  const [isExporting, setIsExporting] = useState(false);

  const handleExportPdf = async () => {
    if (!scannerType || !scanId || isExporting) return;
    setIsExporting(true);
    showToast("Generating official PDF report...", "info");
    try {
      await reportService.exportReportPdf(scannerType, Number(scanId));
      showToast("PDF report downloaded successfully.", "success");
    } catch (err) {
      showToast(extractErrorMessage(err, "Failed to download PDF report."), "error");
    } finally {
      setIsExporting(false);
    }
  };

  if (isLoading) return <LoadingScreen label="Generating report…" />;

  if (error || !report) {
    return (
      <div className="glass-card p-8 text-center">
        <p className="text-sm text-danger">{error ?? "Report not found."}</p>
        <button onClick={() => navigate("/dashboard/scan-center")} className="btn-secondary mt-4">
          <ArrowLeft size={16} />
          Back to Scan Center
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3 print:hidden">
        <Link to="/dashboard/scan-center" className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-200">
          <ArrowLeft size={15} />
          Back to Scan Center
        </Link>
        <div className="flex gap-2">
          <button onClick={handlePrint} className="btn-secondary px-4 py-2 text-xs">
            <Printer size={14} />
            Print
          </button>
          <button onClick={handleShare} className="btn-secondary px-4 py-2 text-xs">
            <Share2 size={14} />
            Share
          </button>
          <button
            onClick={handleExportPdf}
            disabled={isExporting}
            className="btn-secondary px-4 py-2 text-xs disabled:opacity-50"
          >
            <Download size={14} />
            {isExporting ? "Exporting..." : "Export PDF"}
          </button>
        </div>
      </div>

      <div className="glass-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">Security Report · {report.report_id}</p>
            <h1 className="mt-1 text-2xl font-bold text-slate-50">{report.target}</h1>
            <p className="mt-1 text-sm text-slate-500">
              Scanned {formatRelativeDate(report.scan_date)} by {report.user.full_name}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-3xl font-extrabold text-slate-50">{report.trust_score}</span>
            <Badge variant={RISK_VARIANT[report.risk_level]}>{report.risk_level}</Badge>
          </div>
        </div>
      </div>

      <div className="flex gap-2 print:hidden">
        {TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setActiveTab(tab.value)}
            className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-colors ${
              activeTab === tab.value ? "bg-brand-cyan/10 text-brand-cyan" : "text-slate-500 hover:text-slate-300"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* All four sections always render (print needs the full report even
          though only one tab is visible on screen at a time) — each
          section's own className hides it on screen when inactive but
          forces it visible under print media. */}
      <div className={activeTab === "overview" ? "glass-card p-6" : "hidden print:block glass-card p-6"}>
        <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-slate-100">
          <FileText size={16} className="text-slate-400" />
          Overview
        </h2>
        <p className="text-sm leading-relaxed text-slate-300">{report.summary}</p>
      </div>

      <div className={activeTab === "indicators" ? "glass-card p-6" : "hidden print:block glass-card p-6"}>
        <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-slate-100">
          <ShieldAlert size={16} className="text-slate-400" />
          Detected Indicators
        </h2>
        {report.findings.reasons.length === 0 ? (
          <p className="text-sm text-slate-500">No risk indicators were detected.</p>
        ) : (
          <ul className="space-y-2">
            {report.findings.reasons.map((reason, i) => (
              <li key={i} className="text-sm text-slate-300">
                {reason}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className={activeTab === "recommendations" ? "glass-card p-6" : "hidden print:block glass-card p-6"}>
        <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-slate-100">
          <ListChecks size={16} className="text-slate-400" />
          Recommendations
        </h2>
        <ul className="space-y-2">
          {report.recommendations.map((rec, i) => (
            <li key={i} className="text-sm text-slate-300">
              • {rec}
            </li>
          ))}
        </ul>
      </div>

      <div className={activeTab === "technical" ? "glass-card p-6" : "hidden print:block glass-card p-6"}>
        <h2 className="mb-3 text-base font-semibold text-slate-100">Technical Details</h2>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {report.findings.rules.map((rule) => (
            <div key={rule.rule} className="rounded-xl border border-white/5 bg-white/[0.02] px-3 py-2.5">
              <p className="text-xs font-semibold text-slate-300">{rule.label}</p>
              <p className="text-xs text-slate-500">{rule.message}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
