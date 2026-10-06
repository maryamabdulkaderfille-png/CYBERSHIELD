import { motion } from "framer-motion";
import { BarChart3, Bell, Globe2, LayoutGrid, Link2, Mail, QrCode, ShieldCheck } from "lucide-react";

const FEATURES = [
  {
    icon: Link2,
    title: "URL Phishing Detection",
    description:
      "Deep analysis of domain age, SSL, redirects, typosquatting, and blacklist status — with a clear trust score.",
  },
  {
    icon: Mail,
    title: "Email Threat Analysis",
    description: "Detects sender spoofing, urgency language, brand impersonation, and malicious links in emails.",
  },
  {
    icon: QrCode,
    title: "QR Code Scanning",
    description: "Upload any QR code to safely extract and analyze its destination before you ever visit it.",
  },
  {
    icon: ShieldCheck,
    title: "Real-Time Browser Protection",
    description: "A browser extension that warns you before you enter passwords on a dangerous site.",
  },
  {
    icon: LayoutGrid,
    title: "Unified Scan Center",
    description: "Every URL, email, and QR scan in one searchable, filterable, sortable history.",
  },
  {
    icon: BarChart3,
    title: "Security Dashboard",
    description: "A personal security score, threat trends, and activity heat map built from your own scan history.",
  },
  {
    icon: Globe2,
    title: "Threat Intelligence",
    description: "A platform-wide view of known-bad domains, targeted brands, and detection trends.",
  },
  {
    icon: Bell,
    title: "Smart Notifications",
    description: "Automatic alerts the moment a scan crosses into Suspicious or Dangerous territory.",
  },
];

export function FeaturesSection() {
  return (
    <section id="features" className="mx-auto max-w-7xl px-6 py-20">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="mx-auto max-w-2xl text-center"
      >
        <h2 className="text-3xl font-bold text-slate-50">Everything you need to stay safe</h2>
        <p className="mt-3 text-slate-400">
          One platform covering the most common phishing vectors — with more coming as CyberShield grows.
        </p>
      </motion.div>

      <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map(({ icon: Icon, title, description }, index) => (
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
