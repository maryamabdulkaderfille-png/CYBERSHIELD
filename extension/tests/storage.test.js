import { describe, it, expect, beforeEach, vi } from "vitest";
import { createFakeChrome } from "./helpers/fake-chrome.js";
import { loadSharedScripts } from "./helpers/load-scripts.js";

beforeEach(() => {
  delete globalThis.CyberShield;
  delete globalThis.browser;
  globalThis.chrome = createFakeChrome();
  loadSharedScripts();
});

describe("storage.js — settings", () => {
  it("returns defaults when nothing is stored yet", async () => {
    const settings = await globalThis.CyberShield.storage.getSettings();
    expect(settings).toEqual(globalThis.CyberShield.DEFAULT_SETTINGS);
  });

  it("merges partial updates over the current settings, not replacing them", async () => {
    await globalThis.CyberShield.storage.setSettings({ theme: "light" });
    await globalThis.CyberShield.storage.setSettings({ privacyMode: true });
    const settings = await globalThis.CyberShield.storage.getSettings();
    expect(settings.theme).toBe("light");
    expect(settings.privacyMode).toBe(true);
    expect(settings.protectionEnabled).toBe(true); // untouched default preserved
  });
});

describe("storage.js — scan cache", () => {
  it("returns null for a URL that was never cached", async () => {
    const result = await globalThis.CyberShield.storage.getCachedResult("https://example.com");
    expect(result).toBeNull();
  });

  it("returns a fresh cached result within the TTL", async () => {
    const fakeResult = { trust_score: 90, risk: "Safe" };
    await globalThis.CyberShield.storage.setCachedResult("https://example.com", fakeResult);
    const cached = await globalThis.CyberShield.storage.getCachedResult("https://example.com");
    expect(cached).toEqual(fakeResult);
  });

  it("treats an expired cache entry as a miss", async () => {
    vi.useFakeTimers();
    try {
      await globalThis.CyberShield.storage.setCachedResult("https://example.com", { trust_score: 90 });
      vi.advanceTimersByTime(globalThis.CyberShield.CACHE_TTL_MS + 1000);
      const cached = await globalThis.CyberShield.storage.getCachedResult("https://example.com");
      expect(cached).toBeNull();
    } finally {
      vi.useRealTimers();
    }
  });

  it("evicts the oldest entries once the cache exceeds its max size", async () => {
    const max = globalThis.CyberShield.CACHE_MAX_ENTRIES;
    for (let i = 0; i < max + 5; i++) {
      await globalThis.CyberShield.storage.setCachedResult(`https://example.com/${i}`, { trust_score: i });
    }
    const cache = await globalThis.CyberShield.storage.getCache();
    expect(Object.keys(cache).length).toBe(max);
    // the earliest entries should have been evicted
    expect(cache["https://example.com/0"]).toBeUndefined();
    expect(cache[`https://example.com/${max + 4}`]).toBeDefined();
  });

  it("pruneExpiredCache removes only stale entries", async () => {
    vi.useFakeTimers();
    try {
      await globalThis.CyberShield.storage.setCachedResult("https://stale.example.com", { trust_score: 10 });
      vi.advanceTimersByTime(globalThis.CyberShield.CACHE_TTL_MS + 1000);
      await globalThis.CyberShield.storage.setCachedResult("https://fresh.example.com", { trust_score: 90 });
      await globalThis.CyberShield.storage.pruneExpiredCache();
      const cache = await globalThis.CyberShield.storage.getCache();
      expect(cache["https://stale.example.com"]).toBeUndefined();
      expect(cache["https://fresh.example.com"]).toBeDefined();
    } finally {
      vi.useRealTimers();
    }
  });
});

describe("storage.js — stats", () => {
  it("increments the requested counter and records lastScanAt", async () => {
    await globalThis.CyberShield.storage.recordStat("totalScans");
    await globalThis.CyberShield.storage.recordStat("totalScans");
    const stats = await globalThis.CyberShield.storage.getStats();
    expect(stats.totalScans).toBe(2);
    expect(stats.lastScanAt).not.toBeNull();
  });

  it("does not record anything when statisticsCollection is disabled", async () => {
    await globalThis.CyberShield.storage.setSettings({ statisticsCollection: false });
    await globalThis.CyberShield.storage.recordStat("totalScans");
    const stats = await globalThis.CyberShield.storage.getStats();
    expect(stats.totalScans).toBe(0);
  });
});

describe("storage.js — session overrides", () => {
  it("records and reports a 'continue anyway' override for a host", async () => {
    let overrides = await globalThis.CyberShield.storage.getSessionOverrides();
    expect(overrides["phishy.example.com"]).toBeUndefined();

    await globalThis.CyberShield.storage.addSessionOverride("phishy.example.com");
    overrides = await globalThis.CyberShield.storage.getSessionOverrides();
    expect(overrides["phishy.example.com"]).toBeTypeOf("number");
  });
});
