import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

import { HeroBackgroundEffect } from "@/components/landing/HeroBackgroundEffect";
import { HeroVisual } from "@/components/landing/HeroVisual";

interface HeroSectionProps {
  isAuthenticated: boolean;
}

export function HeroSection({ isAuthenticated }: HeroSectionProps) {
  return (
    <section className="relative overflow-hidden px-6 pb-24 pt-20 sm:pt-28">
      <video
        aria-hidden="true"
        autoPlay
        muted
        loop
        playsInline
        preload="auto"
        className="pointer-events-none absolute inset-0 h-full w-full object-cover"
        src="/332264.mp4"
      />
      {/* Darkens the background video so the existing text/CTA contrast is
          unaffected, without hiding it — the video itself is already dark,
          so a lighter overlay than before keeps it clearly visible. */}
      <div className="absolute inset-0 bg-navy-950/50" aria-hidden="true" />
      <div className="absolute inset-0 bg-grid-glow" aria-hidden="true" />
      <HeroBackgroundEffect />
      <div className="relative mx-auto grid max-w-7xl grid-cols-1 items-center gap-14 lg:grid-cols-2 lg:gap-20">
        <div className="text-center lg:text-left">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-7 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-medium text-slate-300"
          >
            <Sparkles size={14} className="text-brand-cyan" aria-hidden="true" />
            Intelligent phishing detection, explained in plain language
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-4xl font-extrabold leading-tight text-slate-50 sm:text-5xl md:text-6xl"
          >
            Cyber<span className="brand-gradient-text">Shield</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mx-auto mt-6 max-w-2xl text-lg text-slate-300 lg:mx-0"
          >
            Intelligent Protection Against Phishing Attacks. CyberShield doesn't just say "safe" or "dangerous" —
            it tells you exactly why, and what to do about it.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-11 flex flex-col items-center justify-center gap-4 sm:flex-row lg:justify-start"
          >
            <Link to={isAuthenticated ? "/dashboard" : "/register"} className="btn-primary px-6 py-3 text-base">
              Get Started <ArrowRight size={18} aria-hidden="true" />
            </Link>
            <Link to="/quick-scan" className="btn-secondary px-6 py-3 text-base">
              Quick Scan
            </Link>
            <a href="#features" className="btn-secondary px-6 py-3 text-base">
              Learn More
            </a>
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.45 }}
            className="mt-10 text-xs uppercase tracking-wide text-slate-500"
          >
            23 detection rules · 3 scan types · real-time browser protection · built for a Phishing Detection System thesis
          </motion.p>
        </div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.25, ease: "easeOut" }}
        >
          <HeroVisual />
        </motion.div>
      </div>
    </section>
  );
}
