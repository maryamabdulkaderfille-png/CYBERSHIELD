/**
 * Content script — asks the background worker for a verdict on the current
 * page and, only if it comes back Dangerous, renders a full-page warning
 * inside a closed shadow root (so the host page's own CSS/JS can't reach in
 * and alter or hide our warning). No scoring/detection logic lives here —
 * it only renders whatever the background worker (and ultimately the
 * CyberShield API) already decided.
 */
(function () {
  const api = CyberShield.browserAPI;
  const { RISK_LEVELS, RISK_EMOJI } = CyberShield;

  const currentUrl = location.href;
  const currentHost = location.host;

  let overlayHost = null;
  let shadowRoot = null;

  /** Phase 9 hard block — the site is on the user's Personal Block List.
   * Deliberately has NO "Continue Anyway" button: a warning can be
   * dismissed, but a block the user (or an auto-block mode) explicitly
   * chose to enforce shouldn't be one click away from bypassing itself. */
  function buildBlockedOverlay(blockedEntry) {
    if (overlayHost) return;

    overlayHost = document.createElement("div");
    overlayHost.id = "cybershield-warning-host";
    shadowRoot = overlayHost.attachShadow({ mode: "closed" });

    const style = document.createElement("style");
    style.textContent = CyberShield.WARNING_CSS;
    shadowRoot.appendChild(style);

    const container = document.createElement("div");
    container.className = "cs-overlay";

    container.innerHTML = `
      <div class="cs-card">
        <div class="cs-header">
          <span class="cs-emoji">🛡️</span>
          <div>
            <h1>CyberShield Protection</h1>
            <p class="cs-sub">Access Blocked — this website was previously identified as phishing.</p>
          </div>
        </div>

        <div class="cs-site-row">
          <span class="cs-label">Website</span>
          <span class="cs-value" title="${escapeHtml(currentUrl)}">${escapeHtml(currentHost)}</span>
        </div>

        <div class="cs-score-row">
          <div class="cs-score">
            <span class="cs-score-value">${escapeHtml(String(blockedEntry.trust_score))}</span>
            <span class="cs-score-max">/ 100</span>
          </div>
          <span class="cs-badge">Blocked</span>
        </div>

        ${blockedEntry.reason ? `<div class="cs-section"><h2>Reason</h2><ul><li>${escapeHtml(blockedEntry.reason)}</li></ul></div>` : ""}

        <div class="cs-actions">
          <button type="button" class="cs-btn cs-btn-primary" data-action="go-back">Go Back</button>
          <button type="button" class="cs-btn cs-btn-secondary" data-action="view-details">View Scan Details</button>
          <button type="button" class="cs-btn cs-btn-ghost" data-action="remove-block">Remove From Block List</button>
        </div>
        <p class="cs-error" data-role="unblock-error" style="display:none; margin: 10px 0 0; font-size: 12px; color: #ef4444; text-align: center;"></p>
        <p class="cs-footer">Protected by CyberShield</p>
      </div>
    `;

    shadowRoot.appendChild(container);
    document.documentElement.appendChild(overlayHost);

    shadowRoot.querySelector('[data-action="go-back"]').addEventListener("click", handleGoBack);
    shadowRoot.querySelector('[data-action="view-details"]').addEventListener("click", () => handleViewBlockedDetails(blockedEntry));
    shadowRoot.querySelector('[data-action="remove-block"]').addEventListener("click", () => handleRemoveFromBlockList(blockedEntry));
  }

  function buildOverlay(result) {
    if (overlayHost) return; // already showing

    overlayHost = document.createElement("div");
    overlayHost.id = "cybershield-warning-host";
    shadowRoot = overlayHost.attachShadow({ mode: "closed" });

    const style = document.createElement("style");
    style.textContent = CyberShield.WARNING_CSS;
    shadowRoot.appendChild(style);

    const container = document.createElement("div");
    container.className = "cs-overlay";

    const reasons = (result.reasons || [])
      .slice(0, 6)
      .map((r) => `<li>${escapeHtml(r)}</li>`)
      .join("");
    const recommendations = (result.recommendations || [])
      .slice(0, 6)
      .map((r) => `<li>${escapeHtml(r)}</li>`)
      .join("");

    container.innerHTML = `
      <div class="cs-card">
        <div class="cs-header">
          <span class="cs-emoji">${RISK_EMOJI[RISK_LEVELS.DANGEROUS]}</span>
          <div>
            <h1>Dangerous website blocked</h1>
            <p class="cs-sub">CyberShield flagged this site as a likely phishing or scam page.</p>
          </div>
        </div>

        <div class="cs-site-row">
          <span class="cs-label">Website</span>
          <span class="cs-value" title="${escapeHtml(currentUrl)}">${escapeHtml(currentHost)}</span>
        </div>

        <div class="cs-score-row">
          <div class="cs-score">
            <span class="cs-score-value">${escapeHtml(String(result.trust_score))}</span>
            <span class="cs-score-max">/ 100</span>
          </div>
          <span class="cs-badge">Dangerous</span>
        </div>

        ${reasons ? `<div class="cs-section"><h2>Why this was flagged</h2><ul>${reasons}</ul></div>` : ""}
        ${recommendations ? `<div class="cs-section"><h2>Recommendations</h2><ul>${recommendations}</ul></div>` : ""}

        <div class="cs-actions">
          <button type="button" class="cs-btn cs-btn-primary" data-action="go-back">Go Back</button>
          <button type="button" class="cs-btn cs-btn-secondary" data-action="view-report">View Full Report</button>
          <button type="button" class="cs-btn cs-btn-ghost" data-action="continue">Continue Anyway</button>
        </div>
        <p class="cs-footer">Protected by CyberShield</p>
      </div>
    `;

    shadowRoot.appendChild(container);
    document.documentElement.appendChild(overlayHost);

    shadowRoot.querySelector('[data-action="go-back"]').addEventListener("click", handleGoBack);
    shadowRoot.querySelector('[data-action="continue"]').addEventListener("click", () => handleContinue(result));
    shadowRoot.querySelector('[data-action="view-report"]').addEventListener("click", () => handleViewReport(result));
  }

  /** Short, synthesized alarm — two square-wave beeps via the Web Audio API
   * so no audio asset needs to be bundled/shipped. Never lets a sound
   * failure (e.g. autoplay policy blocking an un-gestured AudioContext)
   * affect the warning overlay itself. */
  function playAlertSound() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const now = ctx.currentTime;
      const beeps = [
        { start: 0, freq: 880 },
        { start: 0.22, freq: 660 },
      ];
      beeps.forEach(({ start, freq }) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "square";
        osc.frequency.setValueAtTime(freq, now + start);
        gain.gain.setValueAtTime(0, now + start);
        gain.gain.linearRampToValueAtTime(0.15, now + start + 0.02);
        gain.gain.linearRampToValueAtTime(0, now + start + 0.2);
        osc.connect(gain).connect(ctx.destination);
        osc.start(now + start);
        osc.stop(now + start + 0.22);
      });
      ctx.resume().catch(() => {});
      setTimeout(() => ctx.close().catch(() => {}), 800);
    } catch {
      // Non-critical — the visual warning is what actually protects the user.
    }
  }

  async function maybePlayAlertSound() {
    const { settings } = await api.runtime.sendMessage({ type: "GET_SETTINGS" });
    if (settings?.soundAlerts) playAlertSound();
  }

  function removeOverlay() {
    if (overlayHost) {
      overlayHost.remove();
      overlayHost = null;
      shadowRoot = null;
    }
  }

  function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = String(value);
    return div.innerHTML;
  }

  function handleGoBack() {
    if (history.length > 1) {
      history.back();
    } else {
      api.runtime.sendMessage({ type: "CLOSE_TAB" });
    }
  }

  async function handleContinue(result) {
    await api.runtime.sendMessage({ type: "CONTINUE_ANYWAY", url: currentUrl });
    removeOverlay();
  }

  async function handleViewReport(result) {
    const { settings } = await api.runtime.sendMessage({ type: "GET_SETTINGS" });
    const base = settings.dashboardBaseUrl.replace(/\/$/, "");
    const path = result.id ? `/dashboard/reports/url/${result.id}` : "/dashboard/url-scanner";
    window.open(`${base}${path}`, "_blank", "noopener");
  }

  async function handleViewBlockedDetails(blockedEntry) {
    const { settings } = await api.runtime.sendMessage({ type: "GET_SETTINGS" });
    const base = settings.dashboardBaseUrl.replace(/\/$/, "");
    const path =
      blockedEntry.scan_id && blockedEntry.scanner_type
        ? `/dashboard/reports/${blockedEntry.scanner_type}/${blockedEntry.scan_id}`
        : "/dashboard/protection/blocked";
    window.open(`${base}${path}`, "_blank", "noopener");
  }

  async function handleRemoveFromBlockList(blockedEntry) {
    const errorEl = shadowRoot?.querySelector('[data-role="unblock-error"]');
    const response = await api.runtime.sendMessage({ type: "UNBLOCK_FROM_WARNING", entryId: blockedEntry.id });
    if (response?.ok) {
      removeOverlay();
      location.reload();
    } else if (errorEl) {
      errorEl.textContent = response?.error || "Could not remove this site from your block list. Please try again.";
      errorEl.style.display = "";
    }
  }

  async function isOverriddenForThisHost() {
    const { overrides } = await api.runtime.sendMessage({ type: "GET_SESSION_OVERRIDES" });
    return Boolean(overrides && overrides[currentHost]);
  }

  async function evaluateCurrentPage() {
    // Checked first, same as before Phase 9: an active "Continue Anyway"
    // override skips asking the background worker anything at all. A host
    // can't accumulate a stale override that outlives a real block, though
    // — background.js proactively clears any override for a host the
    // moment it becomes hard-blocked (see handleNavigation/GET_OR_SCAN_
    // VERDICT in background.js), so this can never suppress a genuine
    // Personal Block List entry.
    const overridden = await isOverriddenForThisHost();
    if (overridden) return;

    const response = await api.runtime.sendMessage({ type: "GET_OR_SCAN_VERDICT", url: currentUrl });
    if (response?.ok && response.hardBlocked && response.blockedEntry) {
      buildBlockedOverlay(response.blockedEntry);
      maybePlayAlertSound();
      return;
    }

    if (response?.ok && response.result && response.isBlocking) {
      buildOverlay(response.result);
      maybePlayAlertSound();
    }
  }

  api.runtime.onMessage.addListener((message) => {
    if (message?.type === "VERDICT_UPDATED" && message.url === currentUrl) {
      removeOverlay();
      if (message.isBlocking && message.result) {
        buildOverlay(message.result);
        maybePlayAlertSound();
      }
    }
  });

  evaluateCurrentPage();
})();
