/**
 * Thin promise-based wrapper over chrome.storage. Settings live in `sync`
 * storage (tiny, follows the user across signed-in Chrome installs); the
 * scan-result cache and local usage stats live in `local` storage (bigger
 * quota, not meant to roam — Privacy Mode implies "this device only").
 */
(function (global) {
  const CyberShield = global.CyberShield || (global.CyberShield = {});
  const api = CyberShield.browserAPI;
  const { STORAGE_KEYS, DEFAULT_SETTINGS } = CyberShield;

  async function getSettings() {
    const stored = await api.storage.sync.get(STORAGE_KEYS.SETTINGS);
    return { ...DEFAULT_SETTINGS, ...(stored[STORAGE_KEYS.SETTINGS] || {}) };
  }

  async function setSettings(partial) {
    const current = await getSettings();
    const updated = { ...current, ...partial };
    await api.storage.sync.set({ [STORAGE_KEYS.SETTINGS]: updated });
    return updated;
  }

  async function getCache() {
    const stored = await api.storage.local.get(STORAGE_KEYS.SCAN_CACHE);
    return stored[STORAGE_KEYS.SCAN_CACHE] || {};
  }

  async function setCache(cache) {
    await api.storage.local.set({ [STORAGE_KEYS.SCAN_CACHE]: cache });
  }

  async function getCachedResult(url) {
    const cache = await getCache();
    const entry = cache[url];
    if (!entry) return null;
    if (Date.now() - entry.cachedAt > CyberShield.CACHE_TTL_MS) return null;
    return entry.result;
  }

  async function setCachedResult(url, result) {
    const cache = await getCache();
    cache[url] = { result, cachedAt: Date.now() };

    const entries = Object.entries(cache);
    if (entries.length > CyberShield.CACHE_MAX_ENTRIES) {
      entries.sort((a, b) => a[1].cachedAt - b[1].cachedAt);
      const trimmed = entries.slice(entries.length - CyberShield.CACHE_MAX_ENTRIES);
      await setCache(Object.fromEntries(trimmed));
      return;
    }
    await setCache(cache);
  }

  async function pruneExpiredCache() {
    const cache = await getCache();
    const now = Date.now();
    const fresh = Object.fromEntries(
      Object.entries(cache).filter(([, entry]) => now - entry.cachedAt <= CyberShield.CACHE_TTL_MS)
    );
    await setCache(fresh);
  }

  const DEFAULT_STATS = {
    totalScans: 0,
    dangerousBlocked: 0,
    suspiciousWarned: 0,
    failedScans: 0,
    lastScanAt: null,
  };

  async function getStats() {
    const stored = await api.storage.local.get(STORAGE_KEYS.STATS);
    return { ...DEFAULT_STATS, ...(stored[STORAGE_KEYS.STATS] || {}) };
  }

  async function recordStat(field) {
    const settings = await getSettings();
    if (!settings.statisticsCollection) return;

    const stats = await getStats();
    stats[field] = (stats[field] || 0) + 1;
    stats.lastScanAt = new Date().toISOString();
    await api.storage.local.set({ [STORAGE_KEYS.STATS]: stats });
  }

  const DEFAULT_PROTECTION_SYNC = { blockedDomains: [], protectionMode: "warn_only", syncedAt: 0 };

  async function getProtectionSync() {
    const stored = await api.storage.local.get(STORAGE_KEYS.PROTECTION_SYNC);
    return { ...DEFAULT_PROTECTION_SYNC, ...(stored[STORAGE_KEYS.PROTECTION_SYNC] || {}) };
  }

  async function setProtectionSync(sync) {
    await api.storage.local.set({ [STORAGE_KEYS.PROTECTION_SYNC]: { ...sync, syncedAt: Date.now() } });
  }

  async function getSessionOverrides() {
    const stored = await api.storage.local.get(STORAGE_KEYS.SESSION_OVERRIDES);
    return stored[STORAGE_KEYS.SESSION_OVERRIDES] || {};
  }

  /** "Continue Anyway" on a dangerous-site warning is remembered so the
   * same origin isn't re-warned on every link click during one browsing
   * session — cleared on browser restart since it's session storage-like
   * (kept in `local` because `session` storage area isn't available in
   * every target browser yet). */
  async function addSessionOverride(origin) {
    const overrides = await getSessionOverrides();
    overrides[origin] = Date.now();
    await api.storage.local.set({ [STORAGE_KEYS.SESSION_OVERRIDES]: overrides });
  }

  /** Called when a host becomes hard-blocked (Phase 9) so a stale "Continue
   * Anyway" from an earlier, softer Dangerous-warning visit can never
   * suppress a block that was explicitly added afterward. */
  async function clearSessionOverride(origin) {
    const overrides = await getSessionOverrides();
    if (!(origin in overrides)) return;
    delete overrides[origin];
    await api.storage.local.set({ [STORAGE_KEYS.SESSION_OVERRIDES]: overrides });
  }

  CyberShield.storage = {
    getSettings,
    setSettings,
    getCache,
    setCache,
    getCachedResult,
    setCachedResult,
    pruneExpiredCache,
    getStats,
    recordStat,
    getSessionOverrides,
    addSessionOverride,
    clearSessionOverride,
    getProtectionSync,
    setProtectionSync,
  };
})(typeof self !== "undefined" ? self : this);
