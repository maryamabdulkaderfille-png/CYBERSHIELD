import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

import { ProtectionFieldBackground } from "@/components/landing/ProtectionFieldBackground";

interface CtaSectionProps {
  isAuthenticated: boolean;
}

export function CtaSection({ isAuthenticated }: CtaSectionProps) {
  return (
    <section className="relative px-6 pb-24">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="glass-card relative mx-auto flex max-w-4xl flex-col items-center gap-6 overflow-hidden px-8 py-14 text-center"
      >
        <video
          aria-hidden="true"
          autoPlay
          muted
          loop
          playsInline
          preload="none"
          className="pointer-events-none absolute inset-0 h-full w-full object-cover"
          src="/8733055-uhd_3840_2160_30fps.mp4"
        />
        {/* Darkens the globe video so it reads as a "worldwide protection"
            backdrop for the closing card, matching the same overlay
            treatment used everywhere else a background video was added. */}
        <div className="absolute inset-0 bg-navy-950/70" aria-hidden="true" />
        <ProtectionFieldBackground />
        {/* Slow ambient glow pulse behind the closing card — a quiet,
            distinct "final beat" motif that gently draws the eye to the CTA. */}
        <motion.div
          aria-hidden="true"
          className="pointer-events-none absolute left-1/2 top-1/2 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-brand-cyan/20 blur-3xl"
          animate={{ opacity: [0.4, 0.8, 0.4], scale: [1, 1.15, 1] }}
          transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
        />
        <h2 className="relative text-3xl font-bold text-slate-50">Ready to protect yourself and your team?</h2>
        <p className="relative max-w-xl text-slate-400">
          Create a free CyberShield account and start scanning suspicious links, emails, and QR codes today.
        </p>
        <Link
          to={isAuthenticated ? "/dashboard" : "/register"}
          className="btn-primary relative px-6 py-3 text-base"
        >
          Get Started <ArrowRight size={18} aria-hidden="true" />
        </Link>
      </motion.div>
    </section>
  );
}
