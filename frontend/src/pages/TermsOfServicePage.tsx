export function TermsOfServicePage() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-20">
      <h1 className="text-3xl font-bold text-slate-50">Terms of Service</h1>
      <p className="mt-2 text-sm text-slate-500">
        CyberShield is an academic thesis project ("Phishing Detection System"), provided for demonstration,
        research, and portfolio purposes.
      </p>

      <div className="glass-card mt-8 space-y-6 p-6 sm:p-8">
        <section>
          <h2 className="text-lg font-semibold text-slate-100">No warranty</h2>
          <p className="mt-2 text-sm text-slate-400">
            CyberShield is provided "as is," without warranty of any kind. Trust scores and risk labels are
            heuristic signals, not a guarantee that any URL, email, or QR code is safe or unsafe. Always use your
            own judgment for anything security-critical.
          </p>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-slate-100">Acceptable use</h2>
          <p className="mt-2 text-sm text-slate-400">
            Don't use CyberShield to scan content you don't have the right to analyze, to attempt to overload or
            abuse the service, or to attempt unauthorized access to other accounts or the admin area.
          </p>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-slate-100">Accounts</h2>
          <p className="mt-2 text-sm text-slate-400">
            You're responsible for keeping your login credentials confidential. You can deactivate your account at
            any time from Settings.
          </p>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-slate-100">Changes</h2>
          <p className="mt-2 text-sm text-slate-400">
            As a student/portfolio project, these terms may change as CyberShield evolves. Material changes will be
            reflected on this page.
          </p>
        </section>
        <p className="border-t border-white/10 pt-4 text-xs text-slate-600">
          This is a thesis/demonstration project, not a commercial service. If CyberShield is deployed for real use
          later, these terms should be reviewed by a qualified professional before going live.
        </p>
      </div>
    </div>
  );
}
