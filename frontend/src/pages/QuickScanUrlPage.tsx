import { motion } from "framer-motion";
import { Loader2, ScanLine, ShieldCheck, X } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { ScanResultCard } from "@/components/scanner/ScanResultCard";
import { extractErrorMessage } from "@/lib/errors";
import * as guestScanService from "@/services/guestScanService";
import type { ScanReport } from "@/types/scan";

const EXAMPLE_URLS = [
  { label: "Safe URL", url: "https://example.com" },
  { label: "Low Risk URL", url: "https://login.example.com/authentication/required" },
  { label: "Suspicious URL", url: "http://secure-login-verify-account.example.net/bank-wallet" },
  { label: "Dangerous URL", url: "http://8.8.8.8/secure-login-verify-account-password" },
];

export function QuickScanUrlPage() {
  const [url, setUrl] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ScanReport | null>(null);

  const handleScan = async (event?: FormEvent) => {
    event?.preventDefault();
    if (!url.trim()) return;

    setError(null);
    setIsScanning(true);
    setReport(null);
    try {
      const result = await guestScanService.guestScanUrl(url.trim());
      setReport(result);
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
    <div className="mx-auto max-w-4xl px-6 py-16">
      <Link to="/quick-scan" className="text-xs font-medium text-slate-500 hover:text-slate-300">
        ← Back to Quick Scan
      </Link>

      <div className="mt-4">
        <h1 className="text-2xl font-bold text-slate-50">Check Link</h1>
        <p className="mt-1 text-sm text-slate-400">
          Paste a link to check it for phishing indicators — trust score, risk level, and a full explanation. No
          account required — guest scan results are not saved to your account.
        </p>
      </div>

      <div className="glass-card mt-6 p-6">
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
        <div className="glass-card mt-6 flex flex-col items-center gap-4 p-10">
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

      {report && !isScanning && (
        <div className="mt-6">
          <ScanResultCard report={report} />
          <p className="mt-6 text-center text-xs text-slate-500">
            Want to keep your scan history?{" "}
            <Link to="/register" className="font-medium text-brand-cyan hover:underline">
              Create a free account
            </Link>
            .
          </p>
        </div>
      )}
    </div>
  );
}
