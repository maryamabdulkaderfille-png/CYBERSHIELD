import { motion } from "framer-motion";
import { BarChart3, ScanSearch, ShieldAlert } from "lucide-react";

const STEPS = [
  { icon: ScanSearch, title: "Submit a target", description: "Paste a URL, forward an email, or upload a QR code." },
  { icon: BarChart3, title: "We analyze it", description: "Our engine checks dozens of phishing indicators instantly." },
  { icon: ShieldAlert, title: "Get a clear verdict", description: "See a trust score, the exact reasons, and what to do next." },
];

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="mx-auto max-w-7xl px-6 py-20">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="mx-auto max-w-2xl text-center"
      >
        <h2 className="text-3xl font-bold text-slate-50">How it works</h2>
        <p className="mt-3 text-slate-400">Three steps between you and a confident answer.</p>
      </motion.div>

      <div className="relative mt-14 grid grid-cols-1 gap-8 sm:grid-cols-3">
        {/* Connecting line linking the three steps — draws in left-to-right
            as the section scrolls into view, reinforcing the "sequence"
            narrative that makes this section distinct from the grid cards
            elsewhere on the page. */}
        <motion.div
          aria-hidden="true"
          initial={{ scaleX: 0 }}
          whileInView={{ scaleX: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 1, delay: 0.2, ease: "easeInOut" }}
          className="absolute left-[16%] right-[16%] top-7 hidden h-px origin-left bg-gradient-to-r from-brand-blue via-brand-cyan to-brand-blue opacity-40 sm:block"
        />

        {STEPS.map(({ icon: Icon, title, description }, index) => (
          <motion.div
            key={title}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
            className="relative text-center"
          >
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-blue to-brand-cyan shadow-glow">
              <Icon size={24} className="text-navy-950" aria-hidden="true" />
            </div>
            <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-slate-500">Step {index + 1}</p>
            <h3 className="mt-1 text-lg font-semibold text-slate-100">{title}</h3>
            <p className="mt-2 text-sm text-slate-400">{description}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
