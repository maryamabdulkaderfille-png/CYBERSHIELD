/**
 * Shared API client — reuses the exact same cookie + CSRF double-submit
 * auth the web dashboard uses (see frontend/src/lib/api.ts): the user logs
 * in via the CyberShield website in this browser, and the extension rides
 * those httpOnly session cookies. No separate login flow is implemented
 * here — that would duplicate auth UI/logic the dashboard already owns.
 *
 * Reads CSRF cookies via chrome.cookies rather than document.cookie because
 * this file also runs inside the background service worker, which has no
 * DOM/document access at all.
 */
(function (global) {
  const CyberShield = global.CyberShield || (global.CyberShield = {});
  const api = CyberShield.browserAPI;

  class ApiError extends Error {
    constructor(message, status, details) {
      super(message);
      this.name = "ApiError";
      this.status = status;
      this.details = details || null;
    }
  }

  function originOf(url) {
    try {
      return new URL(url).origin;
    } catch {
      return url;
    }
  }

  async function getCookie(baseUrl, name) {
    if (!api.cookies || !api.cookies.get) return null;
    try {
      const cookie = await api.cookies.get({ url: originOf(baseUrl), name });
      return cookie ? cookie.value : null;
    } catch {
      return null;
    }
  }

  let refreshPromise = null;

  async function refreshAccessToken(settings) {
    const csrfToken = await getCookie(settings.apiBaseUrl, "csrf_refresh_token");
    const response = await fetch(`${settings.apiBaseUrl}/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: csrfToken ? { "X-CSRF-TOKEN": csrfToken } : {},
    });
    if (!response.ok) {
      throw new ApiError("Session refresh failed.", response.status);
    }
  }

  async function request(path, { method = "GET", body, settings, extraHeaders, _retried = false } = {}) {
    if (!settings || !settings.apiBaseUrl) {
      throw new ApiError("CyberShield extension is not configured (missing API URL).", 0);
    }

    const headers = { "Content-Type": "application/json", ...extraHeaders };
    const isMutating = method !== "GET";
    if (isMutating && path !== "/auth/refresh") {
      const csrfToken = await getCookie(settings.apiBaseUrl, "csrf_access_token");
      if (csrfToken) headers["X-CSRF-TOKEN"] = csrfToken;
    }

    let response;
    try {
      response = await fetch(`${settings.apiBaseUrl}${path}`, {
        method,
        credentials: "include",
        headers,
        body: body ? JSON.stringify(body) : undefined,
      });
    } catch (networkError) {
      throw new ApiError("Could not reach the CyberShield API. Check your connection.", 0);
    }

    if (response.status === 401 && !_retried && path !== "/auth/refresh") {
      try {
        refreshPromise ??= refreshAccessToken(settings).finally(() => {
          refreshPromise = null;
        });
        await refreshPromise;
        return request(path, { method, body, settings, extraHeaders, _retried: true });
      } catch {
        throw new ApiError("Not signed in to CyberShield.", 401);
      }
    }

    let data = null;
    try {
      data = await response.json();
    } catch {
      data = null;
    }

    if (!response.ok) {
      throw new ApiError((data && data.error) || `Request failed (${response.status}).`, response.status, data && data.details);
    }

    return data;
  }

  async function checkAuth(settings) {
    try {
      await request("/users/me", { settings });
      return true;
    } catch {
      return false;
    }
  }

  /** Privacy Mode routes through the minimal, non-persisting
   * /extension/scan endpoint (Phase 6); otherwise this reuses the exact
   * same /url/scan endpoint the web dashboard's URL Scanner page calls —
   * no duplicate scanning endpoint for the default path. The
   * X-CyberShield-Client header (Phase 7) is how the backend tags a
   * persisted scan's `source` as "extension" vs. "web" for admin Scan
   * Management — harmless to send on the privacy-mode path too, since
   * that endpoint doesn't persist anything to tag in the first place. */
  async function scanUrl(url, settings) {
    const path = settings.privacyMode ? "/extension/scan" : "/url/scan";
    return request(path, {
      method: "POST",
      body: { url },
      settings,
      extraHeaders: { "X-CyberShield-Client": "extension" },
    });
  }

  // --- Phase 9: Active Protection & Smart Blocking -------------------------

  /** Polled periodically (see background.js) rather than on every
   * navigation — enforcement reads the local cache storage.js keeps in
   * sync, never blocking the hot navigation path on a network call. */
  async function getProtectionSync(settings) {
    return request("/protection/sync", { settings, extraHeaders: { "X-CyberShield-Client": "extension" } });
  }

  /** Used only when Active Protection is set to an auto-block mode — the
   * extension adds the domain to the user's Personal Block List itself,
   * exactly as if the user had clicked "Block Website" on the dashboard. */
  async function blockWebsite(target, trustScore, riskLevel, reasons, settings, scanId) {
    return request("/protection/blocklist", {
      method: "POST",
      body: { target, trust_score: trustScore, risk_level: riskLevel, reasons, scanner_type: "url", scan_id: scanId ?? null },
      settings,
      extraHeaders: { "X-CyberShield-Client": "extension" },
    });
  }

  async function unblockWebsite(entryId, settings) {
    return request(`/protection/blocklist/${entryId}`, {
      method: "DELETE",
      settings,
      extraHeaders: { "X-CyberShield-Client": "extension" },
    });
  }

  /** Tells the backend the extension just hard-enforced a block, so it can
   * record a real "Extension Blocked Access" notification (Feature 9) —
   * this is never faked client-side only. */
  async function reportExtensionBlockedEvent(domain, settings) {
    return request("/protection/extension-blocked-event", {
      method: "POST",
      body: { domain },
      settings,
      extraHeaders: { "X-CyberShield-Client": "extension" },
    });
  }

  CyberShield.ApiError = ApiError;
  CyberShield.api = {
    request,
    checkAuth,
    scanUrl,
    refreshAccessToken,
    getProtectionSync,
    blockWebsite,
    unblockWebsite,
    reportExtensionBlockedEvent,
  };
})(typeof self !== "undefined" ? self : this);
