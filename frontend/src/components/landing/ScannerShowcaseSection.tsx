import { AnimatePresence, motion } from "framer-motion";
import { Link2, Mail, QrCode } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/common/Badge";
import { ScannerFlowBackground } from "@/components/landing/ScannerFlowBackground";
import { TrustScoreGauge } from "@/components/scanner/TrustScoreGauge";
import type { RiskLevel } from "@/types/scan";

interface ShowcaseTab {
  key: string;
  icon: typeof Link2;
  label: string;
  target: string;
  score: number;
  risk: RiskLevel;
  reasons: string[];
}

const TABS: ShowcaseTab[] = [
  {
    key: "url",
    icon: Link2,
    label: "URL Scanner",
    target: "http://acmepay-secure-login.com/verify",
    score: 12,
    risk: "Dangerous",
    reasons: [
      "Domain registered 6 days ago",
      "Typosquats a known brand domain (acmepay.com)",
      "No valid HTTPS certificate",
    ],
  },
  {
    key: "email",
    icon: Mail,
    label: "Email Analyzer",
    target: "\"AcmePay Support\" <support@mail-secure-acmepay.com>",
    score: 18,
    risk: "Dangerous",
    reasons: [
      "Display name references a brand the sender domain doesn't own",
      "Urgent, threat-language subject line",
      "Contains a link flagged Dangerous by the URL engine",
    ],
  },
  {
    key: "qr",
    icon: QrCode,
    label: "QR Scanner",
    target: "QR code → https://bit.ly/3xLoginVerify",
    score: 41,
    risk: "Suspicious",
    reasons: [
      "Destination is a link shortener — real target is hidden",
      "Redirect chain crosses to a different domain",
      "Requests login credentials on arrival",
    ],
  },
];

export function ScannerShowcaseSection() {
  const [activeKey, setActiveKey] = useState(TABS[0].key);
  const active = TABS.find((tab) => tab.key === activeKey) ?? TABS[0];

  return (
    <section id="scanners" className="relative mx-auto max-w-7xl overflow-hidden px-6 py-20">
      <video
        aria-hidden="true"
        autoPlay
        muted
        loop
        playsInline
        preload="auto"
        className="pointer-events-none absolute inset-0 h-full w-full object-cover"
        src="/8387491-uhd_3840_2160_30fps.mp4"
      />
      {/* Darkens the scanning-HUD video so it reads as an atmospheric
          backdrop behind the existing packet-flow canvas and tab UI,
          rather than competing with them for attention. */}
      <div className="absolute inset-0 bg-navy-950/75" aria-hidden="true" />
      <ScannerFlowBackground />
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="relative mx-auto max-w-2xl text-center"
      >
        <h2 className="text-3xl font-bold text-slate-50">One engine, every attack surface</h2>
        <p className="mt-3 text-slate-400">Illustrative example scans — see exactly what CyberShield reports.</p>
      </motion.div>

      <div className="relative mt-10 flex justify-center">
        <div role="tablist" aria-label="Scanner showcase" className="inline-flex flex-wrap justify-center gap-2 rounded-2xl border border-white/10 bg-white/[0.03] p-1.5">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              role="tab"
              aria-selected={activeKey === tab.key}
              onClick={() => setActiveKey(tab.key)}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-colors ${
                activeKey === tab.key ? "bg-brand-cyan/15 text-brand-cyan" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <tab.icon size={16} aria-hidden="true" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="glass-card relative mx-auto mt-8 grid max-w-4xl grid-cols-1 items-center gap-8 overflow-hidden p-8 sm:grid-cols-[auto_1fr]">
        <AnimatePresence mode="wait">
          <motion.div
            key={active.key}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="relative flex justify-center"
          >
            {/* A slow breathing glow behind the gauge, colored by the active
                result — reinforces "this is actively scanning," and gives
                each tab its own subtle visual identity. */}
            <motion.div
              aria-hidden="true"
              className={`absolute h-32 w-32 rounded-full blur-2xl ${
                active.risk === "Dangerous" ? "bg-danger/25" : active.risk === "Suspicious" ? "bg-warning/25" : "bg-safe/25"
              }`}
              animate={{ opacity: [0.5, 1, 0.5], scale: [1, 1.1, 1] }}
              transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
            />
            <TrustScoreGauge score={active.score} risk={active.risk} size={140} />
          </motion.div>
        </AnimatePresence>
        <AnimatePresence mode="wait">
          <motion.div
            key={active.key}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2, delay: 0.03 }}
          >
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={active.risk === "Dangerous" ? "danger" : active.risk === "Suspicious" ? "warning" : "safe"}>
                {active.risk}
              </Badge>
              <span className="truncate font-mono text-xs text-slate-500">{active.target}</span>
            </div>
            <ul className="mt-4 space-y-2">
              {active.reasons.map((reason) => (
                <li key={reason} className="flex items-start gap-2 text-sm text-slate-300">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-danger" aria-hidden="true" />
                  {reason}
                </li>
              ))}
            </ul>
          </motion.div>
        </AnimatePresence>
      </div>
      <p className="relative mx-auto mt-4 max-w-4xl text-center text-xs text-slate-600">
        Illustrative example for demonstration purposes — not a live scan.
      </p>
    </section>
  );
}
