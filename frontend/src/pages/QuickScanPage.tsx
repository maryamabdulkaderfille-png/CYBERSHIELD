import { motion } from "framer-motion";
import { ArrowRight, Mail, QrCode, ScanLine } from "lucide-react";
import { Link } from "react-router-dom";

const OPTIONS = [
  {
    to: "/quick-scan/url",
    icon: ScanLine,
    title: "Check Link",
    description: "Paste a URL to check it for phishing indicators.",
  },
  {
    to: "/quick-scan/email",
    icon: Mail,
    title: "Check Email",
    description: "Paste an email or upload a .eml file to analyze it.",
  },
  {
    to: "/quick-scan/qr",
    icon: QrCode,
    title: "Scan QR",
    description: "Upload or capture a QR code to check what it points to.",
  },
];

export function QuickScanPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-20">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-slate-50 sm:text-4xl">Quick Scan</h1>
        <p className="mx-auto mt-3 max-w-xl text-sm text-slate-400">
          Choose what you want to check. No account required — guest scan results are not saved to your account.
        </p>
      </div>

      <div className="mt-10 grid grid-cols-1 gap-5 sm:grid-cols-3">
        {OPTIONS.map((option, index) => (
          <motion.div
            key={option.to}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.08 }}
          >
            <Link
              to={option.to}
              className="glass-card group flex h-full flex-col items-center gap-3 p-6 text-center transition-colors hover:border-white/20"
            >
              <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-blue to-brand-cyan">
                <option.icon size={22} className="text-navy-950" />
              </span>
              <h2 className="text-base font-semibold text-slate-100">{option.title}</h2>
              <p className="text-sm text-slate-400">{option.description}</p>
              <span className="mt-1 flex items-center gap-1 text-xs font-medium text-brand-cyan opacity-0 transition-opacity group-hover:opacity-100">
                Start <ArrowRight size={14} aria-hidden="true" />
              </span>
            </Link>
          </motion.div>
        ))}
      </div>

      <p className="mt-10 text-center text-xs text-slate-500">
        Want to save your scan history?{" "}
        <Link to="/register" className="font-medium text-brand-cyan hover:underline">
          Create a free account
        </Link>
        .
      </p>
    </div>
  );
}
