export function PrivacyPolicyPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-20">
      <h1 className="text-3xl font-bold text-slate-50">Privacy Policy</h1>
      <p className="mt-2 text-sm text-slate-500">
        CyberShield is an academic thesis project ("Phishing Detection System"). This policy describes, in plain
        terms, what data the platform actually stores and why — not a template disconnected from the real system.
      </p>

      <div className="glass-card mt-8 space-y-6 p-6 sm:p-8">
        <section>
          <h2 className="text-lg font-semibold text-slate-100">What we store</h2>
          <p className="mt-2 text-sm text-slate-400">
            Account details (name, username, email, hashed password), the URLs/email content/QR content you submit
            for scanning, and the resulting scan reports. Passwords are hashed with bcrypt and are never stored or
            logged in plain text.
          </p>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-slate-100">Browser extension</h2>
          <p className="mt-2 text-sm text-slate-400">
            The extension sends the URL of the page you're viewing to CyberShield's backend to be scored, using the
            same account and API as the web dashboard. Enabling Privacy Mode in the extension's options scans a
            page without saving the result to your account history.
          </p>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-slate-100">What we don't do</h2>
          <p className="mt-2 text-sm text-slate-400">
            We don't sell data, share it with third parties, or use it for advertising. There is no analytics or
            tracking pixel on this site beyond what's necessary to run the product itself.
          </p>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-slate-100">Your controls</h2>
          <p className="mt-2 text-sm text-slate-400">
            You can review and delete individual scans from the Scan Center, manage active login sessions from
            Settings, and deactivate your account at any time — all from the dashboard, with no support ticket
            required.
          </p>
        </section>
        <p className="border-t border-white/10 pt-4 text-xs text-slate-600">
          This is a thesis/demonstration project, not a commercial service. If CyberShield is deployed for real use
          later, this policy should be reviewed by a qualified professional before going live.
        </p>
      </div>
    </div>
  );
}
