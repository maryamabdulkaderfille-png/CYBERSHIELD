import { motion } from "framer-motion";
import { FileText, Loader2, Mail, Upload, X } from "lucide-react";
import { useRef, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { EmailScanResultCard } from "@/components/emailScanner/EmailScanResultCard";
import { extractErrorMessage } from "@/lib/errors";
import * as guestScanService from "@/services/guestScanService";
import type { EmailScanReport } from "@/types/emailScan";

const EXAMPLE_EMAIL = `From: "PayPal Support" <support@mail-secure-paypal.com>
Subject: Urgent: Your Account Will Be Suspended
Content-Type: multipart/mixed; boundary="XYZ"

--XYZ
Content-Type: text/plain; charset="utf-8"

Dear Customer,

We have detected unusual activity on your account. You must verify your identity immediately or your account will be suspended within 24 hours.

Please click the link below to confirm your information:
http://paypa1-secure-login.com/verify

Act now to avoid permanent suspension.

Thank you,
PayPal Security Team

--XYZ
Content-Type: application/octet-stream; name="invoice.pdf.exe"
Content-Disposition: attachment; filename="invoice.pdf.exe"
Content-Transfer-Encoding: base64

QQ==
--XYZ--
`;

type InputMode = "paste" | "upload";

export function QuickScanEmailPage() {
  const [mode, setMode] = useState<InputMode>("paste");
  const [emailText, setEmailText] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<EmailScanReport | null>(null);

  const handleAnalyze = async (event?: FormEvent) => {
    event?.preventDefault();
    if (mode === "paste" && !emailText.trim()) return;
    if (mode === "upload" && !selectedFile) return;

    setError(null);
    setIsScanning(true);
    setReport(null);

    try {
      const result =
        mode === "paste"
          ? await guestScanService.guestScanEmailText(emailText.trim())
          : await guestScanService.guestScanEmailFile(selectedFile!);
      setReport(result);
    } catch (err) {
      setError(extractErrorMessage(err, "Could not analyze this email. Please check it and try again."));
    } finally {
      setIsScanning(false);
    }
  };

  const handleClear = () => {
    setEmailText("");
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    setReport(null);
    setError(null);
  };

  const handleLoadExample = () => {
    setMode("paste");
    setEmailText(EXAMPLE_EMAIL);
    setReport(null);
    setError(null);
  };

  const canAnalyze = mode === "paste" ? emailText.trim().length > 0 : selectedFile !== null;

  return (
    <div className="mx-auto max-w-4xl px-6 py-16">
      <Link to="/quick-scan" className="text-xs font-medium text-slate-500 hover:text-slate-300">
        ← Back to Quick Scan
      </Link>

      <div className="mt-4">
        <h1 className="text-2xl font-bold text-slate-50">Check Email</h1>
        <p className="mt-1 text-sm text-slate-400">
          Paste an email or upload a .eml file to check it for phishing indicators. No account required — guest scan
          results are not saved to your account.
        </p>
      </div>

      <div className="glass-card mt-6 p-6">
        <div className="mb-4 flex gap-2">
          <button
            type="button"
            onClick={() => setMode("paste")}
            className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-colors ${
              mode === "paste" ? "bg-brand-cyan/10 text-brand-cyan" : "text-slate-500 hover:text-slate-300"
            }`}
          >
            Paste Email Content
          </button>
          <button
            type="button"
            onClick={() => setMode("upload")}
            className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-colors ${
              mode === "upload" ? "bg-brand-cyan/10 text-brand-cyan" : "text-slate-500 hover:text-slate-300"
            }`}
          >
            Upload Email File
          </button>
        </div>

        <form onSubmit={handleAnalyze} className="flex flex-col gap-4">
          {mode === "paste" ? (
            <textarea
              value={emailText}
              onChange={(e) => setEmailText(e.target.value)}
              placeholder="Paste the suspicious email here..."
              rows={10}
              disabled={isScanning}
              className="input-field resize-y font-mono text-xs leading-relaxed"
            />
          ) : (
            <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-white/15 bg-white/[0.02] px-6 py-10 text-center transition-colors hover:border-white/25">
              <Upload size={22} className="text-slate-500" />
              <span className="text-sm text-slate-300">
                {selectedFile ? selectedFile.name : "Click to choose a .eml or .msg file"}
              </span>
              <span className="text-xs text-slate-500">Max 5 MB</span>
              <input
                ref={fileInputRef}
                type="file"
                accept=".eml,.msg"
                className="hidden"
                disabled={isScanning}
                onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
              />
            </label>
          )}

          <div className="flex flex-wrap gap-3">
            <button type="submit" disabled={isScanning || !canAnalyze} className="btn-primary px-6">
              {isScanning ? <Loader2 size={18} className="animate-spin" /> : <Mail size={18} />}
              {isScanning ? "Analyzing…" : "Analyze Email"}
            </button>
            <button type="button" onClick={handleClear} disabled={isScanning} className="btn-secondary px-5">
              <X size={16} />
              Clear
            </button>
            <button type="button" onClick={handleLoadExample} disabled={isScanning} className="btn-secondary px-5">
              <FileText size={16} />
              Load Example
            </button>
          </div>
        </form>

        {error && <p className="mt-4 text-sm text-danger">{error}</p>}
      </div>

      {isScanning && (
        <div className="glass-card mt-6 flex flex-col items-center gap-4 p-10">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 1.8, ease: "linear" }}
            className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-blue to-brand-cyan"
          >
            <Mail size={26} className="text-navy-950" />
          </motion.div>
          <p className="text-sm text-slate-400">Parsing and analyzing email for phishing indicators…</p>
        </div>
      )}

      {report && !isScanning && (
        <div className="mt-6">
          <EmailScanResultCard report={report} />
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
