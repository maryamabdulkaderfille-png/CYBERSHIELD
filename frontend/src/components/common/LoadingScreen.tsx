import { motion } from "framer-motion";
import { ShieldCheck } from "lucide-react";

export function LoadingScreen({ label = "Securing your session…" }: { label?: string }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-navy-900">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 2.2, ease: "linear" }}
        className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-blue to-brand-cyan shadow-glow"
      >
        <ShieldCheck size={30} className="text-navy-950" strokeWidth={2.5} />
      </motion.div>
      <p className="animate-pulse-slow text-sm font-medium text-slate-400">{label}</p>
    </div>
  );
}
