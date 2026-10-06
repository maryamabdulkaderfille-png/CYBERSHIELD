/**
 * CSS for the full-page warning overlay, as a plain string — it's injected
 * into a closed shadow root (see content.js), which does not inherit
 * page-level stylesheets, so it can't be a manifest-injected .css file.
 * Keeping it isolated in the shadow root also means the host page's own
 * CSS can never visually tamper with or hide the warning.
 *
 * Attached to the shared CyberShield namespace (not a bare top-level
 * `const`) because each file in manifest.json's content_scripts list is its
 * own top-level script scope — a top-level `let`/`const` in one is invisible
 * to another, the same way two separate <script> tags on a page can't see
 * each other's block-scoped declarations. Only assignments onto a shared
 * object (or `var`) cross that boundary.
 */
(function (global) {
  const CyberShield = global.CyberShield || (global.CyberShield = {});
  CyberShield.WARNING_CSS = `
:host, .cs-overlay {
  all: initial;
}
.cs-overlay {
  position: fixed;
  inset: 0;
  z-index: 2147483647;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: radial-gradient(circle at 20% 20%, rgba(59,130,246,0.25), transparent 45%),
              radial-gradient(circle at 80% 0%, rgba(34,211,238,0.18), transparent 45%),
              #05070d;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: #e2e8f0;
  box-sizing: border-box;
}
.cs-overlay * {
  box-sizing: border-box;
}
.cs-card {
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  overflow-y: auto;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 20px;
  padding: 32px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}
.cs-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 20px;
}
.cs-emoji {
  font-size: 36px;
  line-height: 1;
}
.cs-header h1 {
  margin: 0 0 4px;
  font-size: 20px;
  font-weight: 800;
  color: #f8fafc;
}
.cs-sub {
  margin: 0;
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.5;
}
.cs-site-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 10px 14px;
  margin-bottom: 16px;
  gap: 12px;
}
.cs-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}
.cs-value {
  font-size: 13px;
  font-weight: 600;
  color: #f1f5f9;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 320px;
}
.cs-score-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.cs-score {
  display: flex;
  align-items: baseline;
  gap: 4px;
}
.cs-score-value {
  font-size: 34px;
  font-weight: 800;
  color: #ef4444;
}
.cs-score-max {
  font-size: 13px;
  color: #64748b;
}
.cs-badge {
  display: inline-flex;
  align-items: center;
  padding: 5px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  background: rgba(239,68,68,0.15);
  color: #ef4444;
  border: 1px solid rgba(239,68,68,0.35);
}
.cs-section {
  margin-bottom: 16px;
}
.cs-section h2 {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 700;
  color: #cbd5e1;
}
.cs-section ul {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.6;
  color: #94a3b8;
}
.cs-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 24px;
}
.cs-btn {
  flex: 1 1 auto;
  min-width: 120px;
  padding: 11px 16px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  border: 1px solid transparent;
  transition: filter 0.15s ease, background 0.15s ease;
}
.cs-btn-primary {
  background: linear-gradient(135deg, #3b82f6, #22d3ee);
  color: #05070d;
}
.cs-btn-primary:hover {
  filter: brightness(1.1);
}
.cs-btn-secondary {
  background: rgba(255,255,255,0.06);
  color: #e2e8f0;
  border-color: rgba(255,255,255,0.15);
}
.cs-btn-secondary:hover {
  background: rgba(255,255,255,0.1);
}
.cs-btn-ghost {
  background: transparent;
  color: #ef4444;
  border-color: rgba(239,68,68,0.3);
}
.cs-btn-ghost:hover {
  background: rgba(239,68,68,0.08);
}
.cs-footer {
  margin: 18px 0 0;
  text-align: center;
  font-size: 11px;
  color: #475569;
}
`;
})(typeof self !== "undefined" ? self : this);
