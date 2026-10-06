import { motion } from "framer-motion";
import { Quote } from "lucide-react";

const TESTIMONIALS = [
  {
    initials: "AK",
    name: "A. Karimova",
    role: "Security Analyst (Fictional Persona)",
    quote:
      "The trust score alone wouldn't have convinced me — seeing the exact reasons a link was flagged made the difference.",
  },
  {
    initials: "MR",
    name: "M. Rahimov",
    role: "IT Administrator (Fictional Persona)",
    quote:
      "Rolling out the browser extension across a small team took minutes, and the admin panel gave us visibility we didn't have before.",
  },
  {
    initials: "SD",
    name: "S. Davronova",
    role: "University Researcher (Fictional Persona)",
    quote:
      "As a case study, it's rare to see a detection engine that explains its own reasoning this clearly.",
  },
];

export function TestimonialsSection() {
  return (
    <section id="testimonials" className="mx-auto max-w-7xl px-6 py-20">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="mx-auto max-w-2xl text-center"
      >
        <h2 className="text-3xl font-bold text-slate-50">Sample Testimonials</h2>
        <p className="mt-2 inline-block rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-slate-500">
          Demo Testimonials (Fictional Personas) — these fictional testimonials are included for
          demonstration purposes only to showcase the CyberShield user interface. They do not
          represent real users, real organizations, or actual reviews.
        </p>
      </motion.div>

      <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-3">
        {TESTIMONIALS.map(({ initials, name, role, quote }, index) => (
          <motion.figure
            key={name}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            whileHover={{ y: -6 }}
            transition={{ delay: index * 0.08 }}
            className="glass-card flex flex-col gap-4 p-6 transition-colors duration-300 hover:border-brand-cyan/30"
          >
            <Quote size={20} className="text-brand-cyan/60" aria-hidden="true" />
            <blockquote className="flex-1 text-sm text-slate-300">"{quote}"</blockquote>
            <figcaption className="flex items-center gap-3 border-t border-white/10 pt-4">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-blue to-brand-cyan text-xs font-bold text-navy-950">
                {initials}
              </span>
              <span>
                <span className="block text-sm font-semibold text-slate-100">{name}</span>
                <span className="block text-xs text-slate-500">{role}</span>
              </span>
            </figcaption>
          </motion.figure>
        ))}
      </div>
    </section>
  );
}
