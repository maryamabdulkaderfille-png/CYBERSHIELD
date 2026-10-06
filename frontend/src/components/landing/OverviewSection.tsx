import { motion } from "framer-motion";
import { Layers, ShieldCheck, Sparkles } from "lucide-react";

const PILLARS = [
  {
    icon: Sparkles,
    title: "Explain, don't just label",
    description: "Every scan returns a trust score plus the exact rules that fired — never a bare safe/unsafe verdict.",
  },
  {
    icon: Layers,
    title: "One engine, three surfaces",
    description: "The same URL detection engine powers link scanning, email link analysis, and QR code destinations.",
  },
  {
    icon: ShieldCheck,
    title: "Protection where you already are",
    description: "Scan manually in the dashboard, or let the browser extension check pages automatically as you browse.",
  },
];

export function OverviewSection() {
  return (
    <section id="overview" className="relative overflow-hidden px-6 py-20">
      <video
        aria-hidden="true"
        autoPlay
        muted
        loop
        playsInline
        preload="none"
        className="pointer-events-none absolute inset-0 h-full w-full object-cover"
        src="/340193.mp4"
      />
      {/* Darkens the background video so the section's text keeps its
          existing contrast — same treatment as the hero's video background. */}
      <div className="absolute inset-0 bg-navy-950/80" aria-hidden="true" />

      <div className="relative mx-auto max-w-7xl">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mx-auto max-w-2xl text-center"
        >
          <h2 className="text-3xl font-bold text-slate-50">What is CyberShield?</h2>
          <p className="mt-3 text-slate-400">
            CyberShield is a full-stack cybersecurity platform built to detect and explain phishing attempts across
            URLs, emails, and QR codes — with a browser extension for real-time protection and an admin console for
            platform operators.
          </p>
        </motion.div>

        <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-3">
          {PILLARS.map(({ icon: Icon, title, description }, index) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              whileHover={{ y: -6 }}
              transition={{ delay: index * 0.08 }}
              className="group glass-card p-6 text-center transition-colors duration-300 hover:border-brand-cyan/30"
            >
              <div className="mx-auto mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-brand-blue/20 to-brand-cyan/20 text-brand-cyan transition-transform duration-300 group-hover:scale-110">
                <Icon size={22} aria-hidden="true" />
              </div>
              <h3 className="text-base font-semibold text-slate-100">{title}</h3>
              <p className="mt-2 text-sm text-slate-400">{description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
