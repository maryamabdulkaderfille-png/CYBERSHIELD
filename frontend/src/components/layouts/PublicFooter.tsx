import { ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

const PRODUCT_LINKS = [
  { label: "URL Scanner", href: "/#scanners" },
  { label: "Email Analyzer", href: "/#scanners" },
  { label: "QR Scanner", href: "/#scanners" },
  { label: "Browser Extension", href: "/#extension" },
];

const COMPANY_LINKS = [
  { label: "About", href: "/#overview" },
  { label: "Security", href: "/#threat-intelligence" },
  { label: "FAQ", href: "/#faq" },
  { label: "Contact", href: "/#contact" },
];

export function PublicFooter() {
  return (
    <footer className="border-t border-white/5 bg-navy-950/60">
      <div className="mx-auto flex max-w-7xl flex-col gap-8 px-6 py-12 md:flex-row md:justify-between">
        <div className="max-w-sm">
          <div className="flex items-center gap-2 font-bold text-slate-50">
            <ShieldCheck size={20} className="text-brand-cyan" aria-hidden="true" />
            CyberShield
          </div>
          <p className="mt-3 text-sm text-slate-500">
            Intelligent protection against phishing attacks — an academic thesis project ("Phishing Detection
            System") for individuals, organizations, and security teams.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-8 sm:grid-cols-3">
          <nav aria-label="Product">
            <h4 className="text-sm font-semibold text-slate-200">Product</h4>
            <ul className="mt-3 space-y-2 text-sm text-slate-500">
              {PRODUCT_LINKS.map((link) => (
                <li key={link.label}>
                  <a href={link.href} className="transition-colors hover:text-slate-300">
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
          <nav aria-label="Company">
            <h4 className="text-sm font-semibold text-slate-200">Company</h4>
            <ul className="mt-3 space-y-2 text-sm text-slate-500">
              {COMPANY_LINKS.map((link) => (
                <li key={link.label}>
                  <a href={link.href} className="transition-colors hover:text-slate-300">
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
          <nav aria-label="Legal">
            <h4 className="text-sm font-semibold text-slate-200">Legal</h4>
            <ul className="mt-3 space-y-2 text-sm text-slate-500">
              <li>
                <Link to="/privacy-policy" className="transition-colors hover:text-slate-300">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link to="/terms-of-service" className="transition-colors hover:text-slate-300">
                  Terms of Service
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      </div>
      <div className="border-t border-white/5 px-6 py-5 text-center text-xs text-slate-600">
        © {new Date().getFullYear()} CyberShield. Academic thesis project — all rights reserved.
      </div>
    </footer>
  );
}
