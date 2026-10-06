import { describe, it, expect, beforeEach, vi } from "vitest";
import { createFakeChrome } from "./helpers/fake-chrome.js";
import { loadSharedScripts, loadScript } from "./helpers/load-scripts.js";

function jsonResponse(status, body) {
  return { ok: status >= 200 && status < 300, status, json: async () => body };
}

let fakeChrome;

function sendMessage(message, sender = { tab: { id: 1 } }) {
  return new Promise((resolve) => {
    fakeChrome.__listeners.runtimeOnMessage[0](message, sender, resolve);
  });
}

beforeEach(() => {
  delete globalThis.CyberShield;
  delete globalThis.browser;
  fakeChrome = createFakeChrome();
  globalThis.chrome = fakeChrome;
  globalThis.importScripts = vi.fn();
  globalThis.fetch = vi.fn();
  loadSharedScripts();
  loadScript("src/background/background.js");
});

describe("performance — avoiding unnecessary API requests", () => {
  it("a cache hit resolves without ever calling fetch", async () => {
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(201, { trust_score: 95, risk: "Safe" }));
    await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://example.com" });

    const before = globalThis.fetch.mock.calls.length;
    const start = performance.now();
    await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://example.com" });
    const elapsed = performance.now() - start;

    expect(globalThis.fetch.mock.calls.length).toBe(before); // no new network call
    expect(elapsed).toBeLessThan(100); // cache path is effectively synchronous
  });

  it("concurrent requests for the same not-yet-cached URL are de-duplicated into one API call", async () => {
    let resolveFetch;
    globalThis.fetch.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveFetch = resolve;
        })
    );

    const first = sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://slow.example.com" });
    const second = sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 2, url: "https://slow.example.com" });

    // Both requests race through several `await`s (settings, cache lookup)
    // before either reaches the actual fetch() call — wait for that to
    // actually happen before resolving it.
    await vi.waitFor(() => expect(resolveFetch).toBeTypeOf("function"));
    resolveFetch(jsonResponse(201, { trust_score: 88, risk: "Low Risk" }));
    const [r1, r2] = await Promise.all([first, second]);

    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    expect(r1.result.trust_score).toBe(88);
    expect(r2.result.trust_score).toBe(88);
  });

  it("expired cache entries are pruned so storage doesn't grow unbounded", async () => {
    vi.useFakeTimers();
    try {
      for (let i = 0; i < 10; i++) {
        await globalThis.CyberShield.storage.setCachedResult(`https://example.com/${i}`, { trust_score: 90 });
      }
      vi.advanceTimersByTime(globalThis.CyberShield.CACHE_TTL_MS + 1000);
      await globalThis.CyberShield.storage.pruneExpiredCache();
      const cache = await globalThis.CyberShield.storage.getCache();
      expect(Object.keys(cache)).toHaveLength(0);
    } finally {
      vi.useRealTimers();
    }
  });
});

describe("performance — rate limiter resets after its window elapses", () => {
  it("allows requests again once the sliding window has passed", async () => {
    vi.useFakeTimers();
    try {
      globalThis.fetch.mockResolvedValue(jsonResponse(201, { trust_score: 95, risk: "Safe" }));
      const max = globalThis.CyberShield.RATE_LIMIT_MAX_REQUESTS;

      for (let i = 0; i < max; i++) {
        await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: `https://example.com/${i}` });
      }
      expect(globalThis.fetch).toHaveBeenCalledTimes(max);

      // still within the window — throttled
      await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://example.com/blocked" });
      expect(globalThis.fetch).toHaveBeenCalledTimes(max);

      vi.advanceTimersByTime(globalThis.CyberShield.RATE_LIMIT_WINDOW_MS + 1000);

      await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://example.com/after-window" });
      expect(globalThis.fetch).toHaveBeenCalledTimes(max + 1);
    } finally {
      vi.useRealTimers();
    }
  });
});
