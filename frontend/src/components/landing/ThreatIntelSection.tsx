import { motion } from "framer-motion";
import { Fingerprint, Radar, ShieldBan, TrendingUp } from "lucide-react";

import { ThreatMapBackground } from "@/components/landing/ThreatMapBackground";

const CAPABILITIES = [
  {
    icon: ShieldBan,
    title: "Known-bad domain database",
    description: "A maintained blacklist checked on every URL scan — manageable directly from the admin panel.",
  },
  {
    icon: Fingerprint,
    title: "Brand impersonation tracking",
    description: "Recognizes when a link or email spoofs a known brand's identity instead of its real domain.",
  },
  {
    icon: TrendingUp,
    title: "Detection trends",
    description: "Platform-wide view of the keywords, domains, and categories showing up most across every scan.",
  },
  {
    icon: Radar,
    title: "Extensible threat feed architecture",
    description: "Built behind a swappable provider interface, ready for a live external threat feed later.",
  },
];

export function ThreatIntelSection() {
  return (
    <section id="threat-intelligence" className="relative mx-auto max-w-7xl overflow-hidden px-6 py-20">
      {/* Slow rotating radar sweep — a faint conic gradient, unique to this
          section and thematically tied to "threat intelligence"/monitoring. */}
      <motion.div
        aria-hidden="true"
        className="pointer-events-none absolute left-1/2 top-1/2 h-[720px] w-[720px] -translate-x-1/2 -translate-y-1/2 rounded-full opacity-[0.07] blur-2xl"
        style={{
          background: "conic-gradient(from 0deg, transparent 0deg, #22d3ee 25deg, transparent 70deg, transparent 360deg)",
        }}
        animate={{ rotate: 360 }}
        transition={{ duration: 14, repeat: Infinity, ease: "linear" }}
      />
      <ThreatMapBackground />

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="relative mx-auto max-w-2xl text-center"
      >
        <h2 className="text-3xl font-bold text-slate-50">Threat Intelligence, platform-wide</h2>
        <p className="mt-3 text-slate-400">
          CyberShield doesn't just protect one account — it aggregates patterns across every scan to build a
          clearer picture of what's actually being seen.
        </p>
      </motion.div>

      <div className="relative mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {CAPABILITIES.map(({ icon: Icon, title, description }, index) => (
          <motion.div
            key={title}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            whileHover={{ y: -6 }}
            transition={{ delay: (index % 4) * 0.08 }}
            className="group glass-card p-6 transition-colors duration-300 hover:border-brand-cyan/30"
          >
            <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-brand-blue/20 to-brand-cyan/20 text-brand-cyan transition-transform duration-300 group-hover:scale-110">
              <Icon size={22} aria-hidden="true" />
            </div>
            <h3 className="text-base font-semibold text-slate-100">{title}</h3>
            <p className="mt-2 text-sm text-slate-400">{description}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
