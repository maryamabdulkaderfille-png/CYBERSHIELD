import { useState } from "react";
import { motion } from "framer-motion";
import { Bell, Chrome, Download, Gauge, HelpCircle, ShieldAlert } from "lucide-react";

const EXTENSION_FEATURES = [
  { icon: ShieldAlert, text: "Full-page warning before you land on a dangerous site" },
  { icon: Gauge, text: "Live trust score for the site you're currently on" },
  { icon: Bell, text: "Browser notifications the moment a threat is detected" },
];

export function ExtensionShowcaseSection() {
  const [showInstallGuide, setShowInstallGuide] = useState(false);
  return (
    <section id="extension" className="mx-auto max-w-7xl px-6 py-20">
      <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
        >
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-slate-300">
            <Chrome size={14} className="text-brand-cyan" aria-hidden="true" />
            Chrome & Edge · Manifest V3
          </div>
          <h2 className="text-3xl font-bold text-slate-50">Protection that follows you online</h2>
          <p className="mt-3 text-slate-400">
            The CyberShield browser extension scans pages automatically as you browse, using the exact same
            detection engine as the web dashboard — so a page flagged by the extension shows up in your real scan
            history too, not a separate silo.
          </p>
          <ul className="mt-6 space-y-3">
            {EXTENSION_FEATURES.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-center gap-3 text-sm text-slate-300">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-cyan/10 text-brand-cyan">
                  <Icon size={16} aria-hidden="true" />
                </span>
                {text}
              </li>
            ))}
          </ul>

          <div className="mt-8 flex flex-wrap items-center gap-4">
            <a
              href="/cybershield-extension.zip"
              download="cybershield-extension.zip"
              className="btn-primary inline-flex items-center gap-2 px-5 py-3 text-sm"
            >
              <Download size={16} />
              Download Extension (ZIP)
            </a>
            <button
              type="button"
              onClick={() => setShowInstallGuide((prev) => !prev)}
              className="inline-flex items-center gap-1.5 text-xs text-brand-cyan hover:underline"
            >
              <HelpCircle size={14} />
              How to install in Chrome / Edge
            </button>
          </div>

          {showInstallGuide && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 rounded-xl border border-white/10 bg-navy-900/80 p-4 text-xs text-slate-300"
            >
              <p className="font-semibold text-slate-100">Simple 3-step installation:</p>
              <ol className="mt-2 list-decimal space-y-1.5 pl-4 text-slate-400">
                <li>Download and extract (unzip) <code className="text-brand-cyan">cybershield-extension.zip</code>.</li>
                <li>In Chrome or Edge, visit <code className="text-brand-cyan">chrome://extensions</code> and enable <strong>Developer mode</strong> (top right).</li>
                <li>Click <strong>Load unpacked</strong> and select the extracted folder.</li>
              </ol>
            </motion.div>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          aria-hidden="true"
        >
          {/* Continuous gentle float, independent of the entrance animation
              above — makes the preview card feel like it's "hovering," a
              parallax-style touch distinct from the rest of the page. */}
          <motion.div
            animate={{ y: [0, -10, 0] }}
            transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
            className="glass-card p-6"
          >
            <div className="flex items-center gap-2 border-b border-white/10 pb-3">
              <div className="h-3 w-3 rounded-full bg-danger/70" />
              <div className="h-3 w-3 rounded-full bg-warning/70" />
              <div className="h-3 w-3 rounded-full bg-safe/70" />
              <span className="ml-2 truncate text-xs text-slate-500">acmepay-secure-login.com</span>
            </div>
            <div className="mt-5 flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-danger/10 text-2xl font-extrabold text-danger">
                12
              </div>
              <div>
                <p className="text-sm font-semibold text-danger">Dangerous site detected</p>
                <p className="text-xs text-slate-500">CyberShield blocked this page automatically</p>
              </div>
            </div>
            <div className="mt-5 space-y-2 text-xs text-slate-400">
              <p>✔ Domain registered 6 days ago</p>
              <p>✔ Typosquats a known brand domain</p>
              <p>✔ No valid HTTPS certificate</p>
            </div>
            <button type="button" tabIndex={-1} className="btn-secondary mt-5 w-full justify-center text-xs">
              Go Back to Safety
            </button>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
