/**
 * Shared constants — risk-level vocabulary mirrors the backend's
 * app/constants.py RiskLevel exactly (Safe / Low Risk / Suspicious /
 * Dangerous, 90/70/40 thresholds) so nothing here re-implements or
 * re-guesses the scoring the API already computed.
 */
(function (global) {
  const CyberShield = global.CyberShield || (global.CyberShield = {});

  CyberShield.RISK_LEVELS = {
    SAFE: "Safe",
    LOW_RISK: "Low Risk",
    SUSPICIOUS: "Suspicious",
    DANGEROUS: "Dangerous",
  };

  CyberShield.RISK_COLORS = {
    Safe: "#22c55e",
    "Low Risk": "#22d3ee",
    Suspicious: "#eab308",
    Dangerous: "#ef4444",
  };

  CyberShield.RISK_EMOJI = {
    Safe: "🟢",
    "Low Risk": "🟢",
    Suspicious: "🟠",
    Dangerous: "🔴",
  };

  CyberShield.DEFAULT_SETTINGS = {
    protectionEnabled: true,
    autoScan: true,
    notifications: true,
    soundAlerts: true,
    // Trust scores at or below this are treated as blocking-warning
    // territory in the popup/content-script UI. Defaults to the backend's
    // own Dangerous cutoff (score < 40 — see app/constants.py
    // RiskLevel.from_score) so out of the box the extension blocks exactly
    // when the API already says "Dangerous" — raising it (e.g. to 70) makes
    // the extension stricter than the API's own Dangerous/Suspicious line,
    // which is the point of exposing it as a user preference rather than a
    // second hardcoded copy of the thresholds.
    dangerThreshold: 39,
    theme: "system",
    apiBaseUrl: "http://localhost:5000/api/v1",
    dashboardBaseUrl: "http://localhost:5173",
    privacyMode: false,
    statisticsCollection: true,
  };

  CyberShield.STORAGE_KEYS = {
    SETTINGS: "cybershield_settings",
    SCAN_CACHE: "cybershield_scan_cache",
    STATS: "cybershield_stats",
    SESSION_OVERRIDES: "cybershield_session_overrides",
    // Phase 9 — Active Protection: the user's synced Personal Block List
    // ({id, domain} entries) plus their current protection_mode, refreshed
    // periodically and after every block/unblock so enforcement never needs
    // a network round trip on the hot navigation path.
    PROTECTION_SYNC: "cybershield_protection_sync",
  };

  // How often the background worker refreshes the synced block list /
  // protection mode from the API (Phase 9).
  CyberShield.PROTECTION_SYNC_INTERVAL_MINUTES = 10;

  // How long a cached verdict for a URL is considered fresh before the
  // background worker will re-scan it (Part 9: "avoid scanning the same URL
  // repeatedly").
  CyberShield.CACHE_TTL_MS = 5 * 60 * 1000;
  CyberShield.CACHE_MAX_ENTRIES = 200;

  // Client-side budget kept under the backend's own 20/min limiter (see
  // app/routes/v1/scans.py, app/routes/v1/extension.py) so the extension
  // backs off before the server ever has to reject a request.
  CyberShield.RATE_LIMIT_MAX_REQUESTS = 15;
  CyberShield.RATE_LIMIT_WINDOW_MS = 60 * 1000;

  CyberShield.RETRY_BASE_DELAY_MS = 1000;
  CyberShield.RETRY_MAX_ATTEMPTS = 3;

  // Skip these schemes entirely — nothing the API could usefully score.
  CyberShield.SKIPPED_URL_PATTERN = /^(chrome|chrome-extension|edge|about|moz-extension|file|devtools):/i;
})(typeof self !== "undefined" ? self : this);
