import { Lock, ScanLine, ShieldCheck } from "lucide-react";
import { Outlet } from "react-router-dom";

import { Logo } from "@/components/common/Logo";

const HIGHLIGHTS = [
  { icon: ShieldCheck, text: "Real-time phishing risk scoring" },
  { icon: ScanLine, text: "URL, email & QR threat analysis" },
  { icon: Lock, text: "Bank-grade authentication & encryption" },
];

export function AuthLayout() {
  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
      <div className="flex flex-col justify-center px-6 py-12 sm:px-12 lg:px-20">
        <div className="mx-auto w-full max-w-md">
          <div className="mb-8">
            <Logo size="lg" />
          </div>
          <Outlet />
        </div>
      </div>

      <div className="relative hidden overflow-hidden border-l border-white/5 bg-navy-950 lg:flex lg:flex-col lg:justify-center lg:px-16">
        <div className="absolute inset-0 bg-grid-glow" />
        <div className="relative z-10 max-w-md">
          <h2 className="text-3xl font-bold leading-tight text-slate-50">
            Stay ahead of <span className="brand-gradient-text">phishing threats</span>
          </h2>
          <p className="mt-4 text-slate-400">
            CyberShield analyzes suspicious links, emails, and QR codes and tells you exactly why they're
            dangerous — not just whether they are.
          </p>
          <div className="mt-10 space-y-5">
            {HIGHLIGHTS.map(({ icon: Icon, text }) => (
              <div key={text} className="flex items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/5 border border-white/10">
                  <Icon size={18} className="text-brand-cyan" />
                </div>
                <span className="text-sm text-slate-300">{text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
