/**
 * Background service worker — orchestrates real-time page scanning.
 *
 * Everything that decides "is this URL dangerous" is the CyberShield API
 * (POST /url/scan or /extension/scan, both backed by the same
 * app/services/url_scanner engine used everywhere else in the platform).
 * This file only decides *when* to call it (navigation events, cache,
 * rate limiting, retries) and what to do with the answer (badge,
 * notification, message the content script / popup) — no scoring logic
 * of its own.
 */
importScripts(
  "../shared/browser-api.js",
  "../shared/constants.js",
  "../shared/storage.js",
  "../shared/api-client.js"
);

const {
  RISK_LEVELS,
  RISK_COLORS,
  SKIPPED_URL_PATTERN,
  RATE_LIMIT_MAX_REQUESTS,
  RATE_LIMIT_WINDOW_MS,
  PROTECTION_SYNC_INTERVAL_MINUTES,
} = CyberShield;
const api = CyberShield.browserAPI;

// tabId -> { url, result, scannedAt, error }
const tabState = new Map();
// url -> Promise<result> — de-dupes a webNavigation-triggered scan and a
// content-script-triggered scan racing for the exact same navigation.
const inFlightScans = new Map();
// "type:host" -> last-notified timestamp, so revisiting the same dangerous
// site repeatedly doesn't spam notifications (Part 7).
const notificationCooldowns = new Map();
const NOTIFICATION_COOLDOWN_MS = 10 * 60 * 1000;

let requestTimestamps = [];
let isOnline = true;

function hostOf(url) {
  try {
    return new URL(url).host;
  } catch {
    return url;
  }
}

function isScannable(url) {
  return typeof url === "string" && url.length > 0 && !SKIPPED_URL_PATTERN.test(url);
}

// --- Active Protection & Smart Blocking (Phase 9) --------------------------

function hostnameOf(url) {
  try {
    return new URL(url).hostname;
  } catch {
    return "";
  }
}

/** Mirrors app.services.url_scanner.domain_utils.registrable_domain exactly
 * (last two labels) so a domain blocked server-side ("evil.com") matches
 * every subdomain of it here too ("www.evil.com", "login.evil.com", ...). */
function registrableDomain(hostname) {
  const labels = hostname.split(".").filter(Boolean);
  return labels.length >= 2 ? labels.slice(-2).join(".") : hostname;
}

// Approximate private/reserved IPv4 ranges — a client-side defense-in-depth
// check. The authoritative guard is server-side (block_list_service.assert_
// blockable, reusing the same is_public_ip validator the URL scanner's SSRF
// protection uses) — this just makes sure the extension itself never
// *enforces* a block against one of these either, belt-and-suspenders.
const PRIVATE_IPV4_PATTERN = /^(10\.|127\.|0\.|169\.254\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/;

function isNeverBlockable(hostname, settings) {
  if (!hostname) return true;
  if (hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1") return true;
  if (PRIVATE_IPV4_PATTERN.test(hostname)) return true;
  const dashboardHost = hostnameOf(settings.dashboardBaseUrl);
  return Boolean(dashboardHost) && hostname === dashboardHost;
}

/** Checked before any scanning happens — a hard block never needs a network
 * call, since the synced Personal Block List is already cached locally. */
async function findHardBlock(url, settings) {
  const hostname = hostnameOf(url);
  if (isNeverBlockable(hostname, settings)) return null;
  const sync = await CyberShield.storage.getProtectionSync();
  const registrable = registrableDomain(hostname);
  return sync.blockedDomains.find((entry) => entry.domain === registrable) || null;
}

function setBadgeForHardBlock(tabId) {
  api.action.setBadgeText({ tabId, text: "X" });
  api.action.setBadgeBackgroundColor({ tabId, color: RISK_COLORS.Dangerous });
}

async function syncProtection() {
  const settings = await CyberShield.storage.getSettings();
  try {
    const response = await CyberShield.api.getProtectionSync(settings);
    await CyberShield.storage.setProtectionSync({
      blockedDomains: response.blocked_domains,
      protectionMode: response.protection_mode,
    });
  } catch (err) {
    // Not signed in / offline — keep whatever was last synced rather than
    // clearing enforcement based on a transient failure.
    console.warn("CyberShield: protection sync failed", err);
  }
}

/** Only called right after a *fresh* scan (never a cache hit) so an
 * auto-block mode never fires the block API repeatedly for the same visit. */
async function maybeAutoBlock(url, result) {
  const sync = await CyberShield.storage.getProtectionSync();
  const mode = sync.protectionMode;
  const shouldBlock =
    (mode === "auto_block_dangerous" && result.risk === RISK_LEVELS.DANGEROUS) ||
    (mode === "auto_block_dangerous_suspicious" &&
      (result.risk === RISK_LEVELS.DANGEROUS || result.risk === RISK_LEVELS.SUSPICIOUS));
  if (!shouldBlock) return;

  const settings = await CyberShield.storage.getSettings();
  const hostname = hostnameOf(url);
  if (isNeverBlockable(hostname, settings)) return;

  try {
    const response = await CyberShield.api.blockWebsite(url, result.trust_score, result.risk, result.reasons || [], settings, result.id);
    const domain = response.entry.domain;
    if (!sync.blockedDomains.some((entry) => entry.domain === domain)) {
      sync.blockedDomains.push({
        id: response.entry.id,
        domain,
        trust_score: response.entry.trust_score,
        risk_level: response.entry.risk_level,
        reason: (response.entry.reasons || [])[0] || null,
        scanner_type: response.entry.scanner_type,
        scan_id: response.entry.scan_id,
      });
      await CyberShield.storage.setProtectionSync(sync);
    }
  } catch (err) {
    // Already blocked (409), offline, or rejected as never-blockable by the
    // server — non-fatal; the next periodic sync reconciles either way.
    console.warn("CyberShield: auto-block request failed", err);
  }
}

function canMakeRequest() {
  const now = Date.now();
  requestTimestamps = requestTimestamps.filter((t) => now - t < RATE_LIMIT_WINDOW_MS);
  if (requestTimestamps.length >= RATE_LIMIT_MAX_REQUESTS) return false;
  requestTimestamps.push(now);
  return true;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function scanWithRetry(url, settings) {
  let lastError;
  for (let attempt = 0; attempt < CyberShield.RETRY_MAX_ATTEMPTS; attempt++) {
    try {
      return await CyberShield.api.scanUrl(url, settings);
    } catch (err) {
      lastError = err;
      // Don't burn retries on "not logged in" / validation errors — those
      // won't succeed no matter how many times we ask. A server-originated
      // 429 (distinct from the client-local pre-emptive one thrown in
      // getOrScanVerdict, which never reaches this function) means the API
      // itself is telling us to back off, so retrying immediately would
      // fight the rate limiter instead of respecting it.
      if (err instanceof CyberShield.ApiError && (err.status === 401 || err.status === 422 || err.status === 429)) {
        throw err;
      }
      if (attempt < CyberShield.RETRY_MAX_ATTEMPTS - 1) {
        await sleep(CyberShield.RETRY_BASE_DELAY_MS * 2 ** attempt);
      }
    }
  }
  throw lastError;
}

/** The API's own Dangerous/Suspicious labels reflect its fixed 40/70/90
 * thresholds (see app/constants.py RiskLevel.from_score). The user's
 * configurable "Danger Threshold" setting is a separate, stricter-or-looser
 * line specifically for *this extension's* blocking behavior — comparing
 * trust_score directly is what makes that setting actually do something,
 * rather than just being a slider that never affects anything. */
function isBlockingResult(result, settings) {
  return result.trust_score <= settings.dangerThreshold;
}

function setBadgeForResult(tabId, result, settings) {
  const risk = result.risk;
  const blocking = isBlockingResult(result, settings);
  const badgeText = blocking ? "!!" : risk === RISK_LEVELS.SUSPICIOUS ? "!" : "";
  api.action.setBadgeText({ tabId, text: badgeText });
  api.action.setBadgeBackgroundColor({ tabId, color: blocking ? RISK_COLORS.Dangerous : RISK_COLORS[risk] || "#64748b" });
}

function setBadgeForError(tabId) {
  api.action.setBadgeText({ tabId, text: "?" });
  api.action.setBadgeBackgroundColor({ tabId, color: "#64748b" });
}

function clearBadge(tabId) {
  api.action.setBadgeText({ tabId, text: "" });
}

async function maybeNotify(type, title, message, host = "") {
  const settings = await CyberShield.storage.getSettings();
  if (!settings.notifications) return;

  // Keyed by type *and* host: repeatedly revisiting the same dangerous site
  // is throttled, but a different dangerous site is still worth its own
  // notification — a global per-type cooldown would silently swallow the
  // second, unrelated site's warning.
  const key = `${type}:${host}`;
  const last = notificationCooldowns.get(key) || 0;
  if (Date.now() - last < NOTIFICATION_COOLDOWN_MS) return;
  notificationCooldowns.set(key, Date.now());

  try {
    await api.notifications.create(`cybershield-${type}-${Date.now()}`, {
      type: "basic",
      iconUrl: "../../icons/icon128.png",
      title,
      message,
      priority: type === "dangerous" ? 2 : 0,
    });
  } catch (err) {
    // Notifications permission/availability issues should never break scanning.
    console.warn("CyberShield: notification creation failed", err);
  }
}

/** Single entry point for "find out the verdict for this tab/url" — used
 * by both the webNavigation listener and the content script's message, so
 * whichever fires first does the real work and the other gets the same
 * in-flight promise instead of triggering a second API call. */
async function getOrScanVerdict(tabId, url) {
  if (!isScannable(url)) return null;

  const settings = await CyberShield.storage.getSettings();
  if (!settings.protectionEnabled) return null;

  const cached = await CyberShield.storage.getCachedResult(url);
  if (cached) {
    tabState.set(tabId, { url, result: cached, scannedAt: Date.now(), error: null });
    setBadgeForResult(tabId, cached, settings);
    return cached;
  }

  if (inFlightScans.has(url)) {
    return inFlightScans.get(url);
  }

  const scanPromise = (async () => {
    if (!isOnline) {
      await maybeNotify(
        "offline",
        "CyberShield — offline",
        "You're offline, so this page couldn't be checked. It will be scanned once you're back online."
      );
      throw new CyberShield.ApiError("Offline.", 0);
    }

    if (!canMakeRequest()) {
      // Graceful degradation: skip this scan cycle rather than queue
      // indefinitely or hammer the API once the window resets.
      throw new CyberShield.ApiError("Rate limit reached — skipping this scan.", 429);
    }

    const result = await scanWithRetry(url, settings);
    await CyberShield.storage.setCachedResult(url, result);
    await CyberShield.storage.recordStat("totalScans");
    await maybeAutoBlock(url, result);
    if (isBlockingResult(result, settings)) {
      await CyberShield.storage.recordStat("dangerousBlocked");
      await maybeNotify(
        "dangerous",
        "⚠️ Dangerous website blocked",
        `${hostOf(url)} was flagged as Dangerous by CyberShield.`,
        hostOf(url)
      );
    } else if (result.risk === RISK_LEVELS.SUSPICIOUS) {
      await CyberShield.storage.recordStat("suspiciousWarned");
      await maybeNotify(
        "suspicious",
        "CyberShield — suspicious site",
        `${hostOf(url)} looks suspicious. Proceed with caution.`,
        hostOf(url)
      );
    }
    return result;
  })();

  inFlightScans.set(url, scanPromise);

  try {
    const result = await scanPromise;
    tabState.set(tabId, { url, result, scannedAt: Date.now(), error: null });
    setBadgeForResult(tabId, result, settings);
    return result;
  } catch (err) {
    await CyberShield.storage.recordStat("failedScans");
    const message = err instanceof CyberShield.ApiError ? err.message : "Unknown error.";
    tabState.set(tabId, { url, result: null, scannedAt: Date.now(), error: message });
    if (!(err instanceof CyberShield.ApiError) || (err.status !== 401 && err.status !== 429 && err.status !== 0)) {
      setBadgeForError(tabId);
      await maybeNotify(
        "failed",
        "CyberShield — scan failed",
        `Could not check ${hostOf(url)}. Will retry on next visit.`,
        hostOf(url)
      );
    } else if (err.status === 0 && isOnline) {
      // Connection genuinely failed mid-request (not just the offline
      // pre-check above) — still worth a (cooled-down) heads-up.
      await maybeNotify("connection", "CyberShield — connection issue", "Could not reach the CyberShield API.");
    }
    return null;
  } finally {
    inFlightScans.delete(url);
  }
}

async function forceRescan(tabId, url) {
  inFlightScans.delete(url);
  const cache = await CyberShield.storage.getCache();
  delete cache[url];
  await CyberShield.storage.setCache(cache);
  return getOrScanVerdict(tabId, url);
}

// --- Navigation detection -----------------------------------------------

function shouldHandleNavigation(details) {
  return details.frameId === 0 && isScannable(details.url);
}

/** Checks the synced Personal Block List before ever considering a live
 * scan — a hard-blocked domain skips the scan/cache path entirely. */
async function handleNavigation(tabId, url) {
  const settings = await CyberShield.storage.getSettings();
  const blockedEntry = await findHardBlock(url, settings);
  if (blockedEntry) {
    tabState.set(tabId, { url, result: null, hardBlocked: true, blockedEntry, scannedAt: Date.now(), error: null });
    setBadgeForHardBlock(tabId);
    await CyberShield.storage.clearSessionOverride(hostOf(url));
    CyberShield.api.reportExtensionBlockedEvent(blockedEntry.domain, settings).catch(() => {});
    return;
  }
  getOrScanVerdict(tabId, url);
}

api.webNavigation.onCommitted.addListener((details) => {
  if (details.frameId !== 0) return;
  if (shouldHandleNavigation(details)) {
    handleNavigation(details.tabId, details.url);
  } else {
    // Navigated to a non-scannable page (chrome://, about:, ...) — don't
    // leave the previous page's badge showing on an unrelated tab.
    tabState.delete(details.tabId);
    clearBadge(details.tabId);
  }
});

// SPA (pushState/replaceState) navigations don't fire onCommitted again.
api.webNavigation.onHistoryStateUpdated.addListener((details) => {
  if (shouldHandleNavigation(details)) {
    handleNavigation(details.tabId, details.url);
  }
});

api.tabs.onRemoved.addListener((tabId) => {
  tabState.delete(tabId);
});

// --- Connectivity ---------------------------------------------------------

if (typeof self.addEventListener === "function") {
  self.addEventListener("online", () => {
    isOnline = true;
  });
  self.addEventListener("offline", () => {
    isOnline = false;
  });
}
isOnline = typeof self.navigator !== "undefined" ? self.navigator.onLine !== false : true;

// --- Periodic housekeeping (alarms survive service-worker suspension) ----

api.alarms.create("cybershield-cache-cleanup", { periodInMinutes: 15 });
api.alarms.create("cybershield-protection-sync", { periodInMinutes: PROTECTION_SYNC_INTERVAL_MINUTES });
api.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "cybershield-cache-cleanup") {
    CyberShield.storage.pruneExpiredCache();
  } else if (alarm.name === "cybershield-protection-sync") {
    syncProtection();
  }
});

// Sync immediately on a real extension install/update and on a true browser
// startup — NOT as bare top-level code, which would re-run (and re-fetch)
// every time the service worker wakes from idle suspension, not just on an
// actual install or browser start. chrome.storage persists across
// suspend/wake, so the periodic alarm alone is enough to keep it fresh the
// rest of the time.
api.runtime.onInstalled.addListener(() => {
  syncProtection();
});
api.runtime.onStartup.addListener(() => {
  syncProtection();
});

// --- Messages from popup / options / content script ----------------------

api.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    switch (message?.type) {
      case "GET_TAB_STATE": {
        const tabId = message.tabId ?? sender.tab?.id;
        sendResponse({ ok: true, state: tabState.get(tabId) || null });
        return;
      }
      case "GET_OR_SCAN_VERDICT": {
        const tabId = message.tabId ?? sender.tab?.id;
        const settings = await CyberShield.storage.getSettings();
        const blockedEntry = await findHardBlock(message.url, settings);
        if (blockedEntry) {
          tabState.set(tabId, { url: message.url, result: null, hardBlocked: true, blockedEntry, scannedAt: Date.now(), error: null });
          setBadgeForHardBlock(tabId);
          await CyberShield.storage.clearSessionOverride(hostOf(message.url));
          CyberShield.api
          .reportExtensionBlockedEvent(blockedEntry.domain, settings)
          .catch((err) => console.warn("CyberShield: blocked-event report failed", err));
          sendResponse({ ok: true, result: null, isBlocking: false, hardBlocked: true, blockedEntry, error: null });
          return;
        }
        const result = await getOrScanVerdict(tabId, message.url);
        const isBlocking = result ? isBlockingResult(result, settings) : false;
        sendResponse({ ok: true, result, isBlocking, hardBlocked: false, error: tabState.get(tabId)?.error || null });
        return;
      }
      case "RESCAN": {
        const tabId = message.tabId ?? sender.tab?.id;
        const result = await forceRescan(tabId, message.url);
        const settings = await CyberShield.storage.getSettings();
        const isBlocking = result ? isBlockingResult(result, settings) : false;
        if (tabId != null) {
          api.tabs.sendMessage(tabId, { type: "VERDICT_UPDATED", url: message.url, result, isBlocking }).catch(() => {});
        }
        sendResponse({ ok: true, result, isBlocking, error: tabState.get(tabId)?.error || null });
        return;
      }
      case "CONTINUE_ANYWAY": {
        await CyberShield.storage.addSessionOverride(hostOf(message.url));
        sendResponse({ ok: true });
        return;
      }
      case "CLOSE_TAB": {
        const tabId = sender.tab?.id;
        if (tabId != null) {
          api.tabs.remove(tabId).catch(() => {});
        }
        sendResponse({ ok: true });
        return;
      }
      case "GET_SETTINGS": {
        const settings = await CyberShield.storage.getSettings();
        sendResponse({ ok: true, settings });
        return;
      }
      case "GET_SESSION_OVERRIDES": {
        const overrides = await CyberShield.storage.getSessionOverrides();
        sendResponse({ ok: true, overrides });
        return;
      }
      case "UNBLOCK_FROM_WARNING": {
        // "Remove From Block List" on the hard-block warning page (Feature
        // 3) — calls the same unblock endpoint the dashboard's Blocked
        // Websites page uses, then updates the local synced cache
        // immediately so the very next visit isn't blocked again.
        const tabId = message.tabId ?? sender.tab?.id;
        const settings = await CyberShield.storage.getSettings();
        try {
          await CyberShield.api.unblockWebsite(message.entryId, settings);
          const sync = await CyberShield.storage.getProtectionSync();
          sync.blockedDomains = sync.blockedDomains.filter((entry) => entry.id !== message.entryId);
          await CyberShield.storage.setProtectionSync(sync);
          tabState.delete(tabId);
          clearBadge(tabId);
          sendResponse({ ok: true });
        } catch (err) {
          sendResponse({ ok: false, error: err instanceof CyberShield.ApiError ? err.message : "Could not unblock." });
        }
        return;
      }
      case "SYNC_PROTECTION": {
        await syncProtection();
        sendResponse({ ok: true });
        return;
      }
      default:
        sendResponse({ ok: false, error: "Unknown message type." });
    }
  })();
  return true; // keep the message channel open for the async response
});
