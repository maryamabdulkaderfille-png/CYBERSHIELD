import { motion } from "framer-motion";
import { Loader2, ScanLine, ShieldCheck, X } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";

import { BlockWebsitePanel } from "@/components/protection/BlockWebsitePanel";
import { RecentScansList } from "@/components/scanner/RecentScansList";
import { ScanResultCard } from "@/components/scanner/ScanResultCard";
import { extractErrorMessage } from "@/lib/errors";
import * as scanService from "@/services/scanService";
import type { ScanHistoryItem, ScanReport } from "@/types/scan";

const EXAMPLE_URLS = [
  { label: "Safe URL", url: "https://example.com" },
  { label: "Low Risk URL", url: "https://login.example.com/authentication/required" },
  { label: "Suspicious URL", url: "http://secure-login-verify-account.example.net/bank-wallet" },
  { label: "Dangerous URL", url: "http://8.8.8.8/secure-login-verify-account-password" },
];

export function UrlScannerPage() {
  const [url, setUrl] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ScanReport | null>(null);
  const [recentScans, setRecentScans] = useState<ScanHistoryItem[]>([]);
  const [isLoadingRecent, setIsLoadingRecent] = useState(true);

  const loadRecentScans = async () => {
    setIsLoadingRecent(true);
    try {
      const history = await scanService.getScanHistory({ page: 1, per_page: 5 });
      setRecentScans(history.items);
    } catch {
      // Non-critical — the recent-scans panel just stays empty.
    } finally {
      setIsLoadingRecent(false);
    }
  };

  useEffect(() => {
    loadRecentScans();
  }, []);

  const handleScan = async (event?: FormEvent) => {
    event?.preventDefault();
    if (!url.trim()) return;

    setError(null);
    setIsScanning(true);
    setReport(null);
    try {
      const result = await scanService.scanUrl(url.trim());
      setReport(result);
      loadRecentScans();
    } catch (err) {
      setError(extractErrorMessage(err, "Could not scan this URL. Please check it and try again."));
    } finally {
      setIsScanning(false);
    }
  };

  const handleClear = () => {
    setUrl("");
    setReport(null);
    setError(null);
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-50">URL Scanner</h1>
        <p className="mt-1 text-sm text-slate-400">
          Paste a link to check it for phishing indicators — trust score, risk level, and a full explanation.
        </p>
      </div>

      <div className="glass-card p-6">
        <form onSubmit={handleScan} className="flex flex-col gap-4 sm:flex-row">
          <div className="relative flex-1">
            <ScanLine size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              className="input-field pl-11"
              disabled={isScanning}
            />
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={isScanning || !url.trim()} className="btn-primary px-6">
              {isScanning ? <Loader2 size={18} className="animate-spin" /> : <ShieldCheck size={18} />}
              {isScanning ? "Scanning…" : "Scan URL"}
            </button>
            <button type="button" onClick={handleClear} disabled={isScanning} className="btn-secondary px-5">
              <X size={16} />
              Clear
            </button>
          </div>
        </form>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-slate-500">Example URLs:</span>
          {EXAMPLE_URLS.map((example) => (
            <button
              key={example.url}
              type="button"
              onClick={() => setUrl(example.url)}
              disabled={isScanning}
              className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs text-slate-400 transition-colors hover:border-white/20 hover:text-slate-200"
            >
              {example.label}
            </button>
          ))}
        </div>

        {error && <p className="mt-4 text-sm text-danger">{error}</p>}
      </div>

      {isScanning && (
        <div className="glass-card flex flex-col items-center gap-4 p-10">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 1.8, ease: "linear" }}
            className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-blue to-brand-cyan"
          >
            <ShieldCheck size={26} className="text-navy-950" />
          </motion.div>
          <p className="text-sm text-slate-400">Analyzing URL for phishing indicators…</p>
        </div>
      )}

      {report && !isScanning && <ScanResultCard report={report} />}
      {report && !isScanning && <BlockWebsitePanel report={report} />}

      <div className="glass-card p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-100">Recent Scans</h2>
        </div>
        {isLoadingRecent ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : (
          <RecentScansList scans={recentScans} emptyDescription="Scan your first URL above to see it here." />
        )}
      </div>
    </div>
  );
}
