import { motion } from "framer-motion";
import { Mail, MessageSquare } from "lucide-react";

const CONTACT_EMAIL = "maryamabdulkaderfille@gmail.com";

export function ContactSection() {
  return (
    <section id="contact" className="mx-auto max-w-4xl px-6 py-20">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="glass-card relative flex flex-col items-center gap-5 overflow-hidden px-8 py-14 text-center"
      >
        <video
          aria-hidden="true"
          autoPlay
          muted
          loop
          playsInline
          preload="none"
          className="pointer-events-none absolute inset-0 h-full w-full object-cover"
          src="/1111.mp4"
        />
        {/* Darkens the background video so the existing text/button contrast
            is unaffected — same overlay treatment used everywhere else a
            background video was added on this page. */}
        <div className="absolute inset-0 bg-navy-950/80" aria-hidden="true" />
        <span className="relative flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-brand-blue/20 to-brand-cyan/20 text-brand-cyan">
          <MessageSquare size={24} aria-hidden="true" />
        </span>
        <h2 className="relative text-3xl font-bold text-slate-50">Questions or feedback?</h2>
        <p className="relative max-w-xl text-slate-400">
          CyberShield is an academic thesis project ("Phishing Detection System"). If you'd like to discuss it,
          reach out and we'll get back to you.
        </p>
        <button
          type="button"
          onClick={() => {
            window.open(
              `https://mail.google.com/mail/?view=cm&fs=1&to=${CONTACT_EMAIL}`,
              "_blank",
              "noopener,noreferrer"
            );
          }}
          className="btn-primary relative px-6 py-3 text-base"
        >
          <Mail size={18} aria-hidden="true" />
          Email the team
        </button>
      </motion.div>
    </section>
  );
}
