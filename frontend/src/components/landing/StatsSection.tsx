import { motion } from "framer-motion";

import { AnimatedCounter } from "@/components/landing/AnimatedCounter";

const STATS = [
  { value: 3.4, decimals: 1, prefix: "", suffix: "B+", label: "Phishing emails sent daily worldwide" },
  { value: 94, decimals: 0, prefix: "", suffix: "%", label: "Of breaches start with a phishing email" },
  { value: 31, decimals: 0, prefix: "", suffix: "", label: "Built-in detection rules across URL, Email & QR engines" },
  { value: 1, decimals: 0, prefix: "<", suffix: "s", label: "Typical CyberShield scan time" },
];

export function StatsSection() {
  return (
    <section id="stats" className="relative overflow-hidden border-y border-white/5 bg-navy-950/50">
      {/* A slow horizontal "scan line" sweep — a distinct, security-scan-
          themed background motif unique to this section. */}
      <motion.div
        className="pointer-events-none absolute inset-y-0 w-32 bg-gradient-to-r from-transparent via-brand-cyan/[0.06] to-transparent"
        animate={{ left: ["-15%", "115%"] }}
        transition={{ duration: 5, repeat: Infinity, ease: "linear", repeatDelay: 1.5 }}
      />

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="relative mx-auto grid max-w-6xl grid-cols-2 gap-10 px-6 py-16 sm:grid-cols-4"
      >
        {STATS.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
            className="text-center"
          >
            <p className="brand-gradient-text text-3xl font-extrabold sm:text-4xl">
              {/* A 0->1 count-up with 0 decimals can only ever render "0" or
                  "1" — with the "<" prefix that means it shows the
                  nonsensical "<0" for nearly the entire animation before
                  snapping to "<1" at the very end. There's no meaningful
                  intermediate progress to animate for a target this small,
                  so render it as static text instead. */}
              {stat.value <= 1 ? (
                `${stat.prefix}${stat.value.toFixed(stat.decimals)}${stat.suffix}`
              ) : (
                <AnimatedCounter value={stat.value} decimals={stat.decimals} prefix={stat.prefix} suffix={stat.suffix} />
              )}
            </p>
            <p className="mt-2 text-sm text-slate-400">{stat.label}</p>
          </motion.div>
        ))}
      </motion.div>
    </section>
  );
}
