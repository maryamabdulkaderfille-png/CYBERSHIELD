import { motion } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { useState } from "react";

const FAQS = [
  {
    question: "Is CyberShield a real, working product or just a demo?",
    answer:
      "Every scanner, the browser extension, and the admin panel are fully functional — built and tested end-to-end as part of an academic thesis project (\"Phishing Detection System\"). Some enterprise features (like live third-party threat feeds) are intentionally scoped as prepared-but-not-implemented placeholders rather than faked.",
  },
  {
    question: "What exactly does a scan check?",
    answer:
      "URL scans run 13 rules covering HTTPS/SSL, domain age, typosquatting, blacklist status, threat intelligence, redirect chains, and more. Email scans add sender/display-name impersonation, urgency language, and attachment checks. QR scans decode the code and route the content to the right analyzer automatically.",
  },
  {
    question: "Does the browser extension send my browsing history anywhere?",
    answer:
      "The extension only submits the current page's URL to CyberShield's own backend to be scored — the same engine and account as the dashboard. An optional Privacy Mode scans without saving the result to your history at all.",
  },
  {
    question: "Can I run this myself?",
    answer:
      "Yes — the whole stack runs locally via Docker Compose (Postgres, Flask API, and the Vite-served frontend). See the Setup section of the project README for exact steps.",
  },
  {
    question: "Is my data secure?",
    answer:
      "Authentication uses httpOnly JWT cookies with CSRF double-submit protection, bcrypt password hashing, rate limiting, and role-based access control for the admin area. See the Security section of the README for the full review.",
  },
];

export function FaqSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section id="faq" className="mx-auto max-w-4xl px-6 py-20">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="mx-auto max-w-2xl text-center"
      >
        <h2 className="text-3xl font-bold text-slate-50">Frequently asked questions</h2>
      </motion.div>

      <div className="mt-10 space-y-3">
        {FAQS.map((faq, index) => {
          const isOpen = openIndex === index;
          const panelId = `faq-panel-${index}`;
          const buttonId = `faq-button-${index}`;
          return (
            <motion.div
              key={faq.question}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: (index % 5) * 0.06 }}
              className="glass-panel overflow-hidden"
            >
              <h3>
                <button
                  id={buttonId}
                  type="button"
                  aria-expanded={isOpen}
                  aria-controls={panelId}
                  onClick={() => setOpenIndex(isOpen ? null : index)}
                  className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left text-sm font-semibold text-slate-100 transition-colors hover:text-brand-cyan"
                >
                  {faq.question}
                  <ChevronDown
                    size={18}
                    aria-hidden="true"
                    className={`shrink-0 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
                  />
                </button>
              </h3>
              <div
                id={panelId}
                role="region"
                aria-labelledby={buttonId}
                hidden={!isOpen}
                className="px-5 pb-4 text-sm text-slate-400"
              >
                {faq.answer}
              </div>
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}
