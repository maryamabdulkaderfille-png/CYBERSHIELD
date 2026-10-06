import { describe, it, expect, beforeEach, vi } from "vitest";
import { createFakeChrome } from "./helpers/fake-chrome.js";
import { loadSharedScripts, loadScript } from "./helpers/load-scripts.js";

function jsonResponse(status, body) {
  return { ok: status >= 200 && status < 300, status, json: async () => body };
}

function safeResult(overrides = {}) {
  return { trust_score: 95, risk: "Safe", reasons: [], recommendations: [], rules: [], scan_date: "2026-01-01T00:00:00Z", ...overrides };
}

function dangerousResult(overrides = {}) {
  return { trust_score: 10, risk: "Dangerous", reasons: ["Blacklisted"], recommendations: ["Do not proceed."], rules: [], ...overrides };
}

let fakeChrome;

function sendMessage(message, sender = { tab: { id: 1 } }) {
  return new Promise((resolve) => {
    const listener = fakeChrome.__listeners.runtimeOnMessage[0];
    listener(message, sender, resolve);
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

describe("background.js — message handling", () => {
  it("GET_OR_SCAN_VERDICT scans an uncached, protection-enabled URL", async () => {
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(201, safeResult()));
    const response = await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://example.com" });
    expect(response.ok).toBe(true);
    expect(response.result.risk).toBe("Safe");
    expect(response.isBlocking).toBe(false);
  });

  it("flags a Dangerous result as blocking", async () => {
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(201, dangerousResult()));
    const response = await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://phish.example.com" });
    expect(response.isBlocking).toBe(true);
  });

  it("honors a custom, stricter dangerThreshold even for a non-Dangerous risk label", async () => {
    await globalThis.CyberShield.storage.setSettings({ dangerThreshold: 80 });
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(201, safeResult({ trust_score: 75, risk: "Low Risk" })));
    const response = await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://borderline.example.com" });
    expect(response.isBlocking).toBe(true);
  });

  it("does not scan at all when protection is disabled", async () => {
    await globalThis.CyberShield.storage.setSettings({ protectionEnabled: false });
    const response = await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://example.com" });
    expect(response.result).toBeNull();
    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it("GET_TAB_STATE returns null before any scan has happened for that tab", async () => {
    const response = await sendMessage({ type: "GET_TAB_STATE", tabId: 42 });
    expect(response.state).toBeNull();
  });

  it("CONTINUE_ANYWAY records a session override for the URL's host", async () => {
    await sendMessage({ type: "CONTINUE_ANYWAY", url: "https://phish.example.com/login" });
    const { overrides } = await sendMessage({ type: "GET_SESSION_OVERRIDES" });
    expect(overrides["phish.example.com"]).toBeTypeOf("number");
  });

  it("CLOSE_TAB removes the sender's tab", async () => {
    await sendMessage({ type: "CLOSE_TAB" }, { tab: { id: 7 } });
    expect(fakeChrome.tabs.remove).toHaveBeenCalledWith(7);
  });

  it("returns an error for an unknown message type", async () => {
    const response = await sendMessage({ type: "NOT_A_REAL_MESSAGE" });
    expect(response.ok).toBe(false);
  });
});

describe("background.js — caching (performance)", () => {
  it("only calls the API once for repeated visits to the same URL", async () => {
    globalThis.fetch.mockResolvedValue(jsonResponse(201, safeResult()));
    await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://example.com" });
    await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://example.com" });
    await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://example.com" });
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it("RESCAN bypasses the cache and re-calls the API", async () => {
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(201, safeResult({ trust_score: 90 })));
    await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://example.com" });

    globalThis.fetch.mockResolvedValueOnce(jsonResponse(201, safeResult({ trust_score: 70 })));
    const response = await sendMessage({ type: "RESCAN", tabId: 1, url: "https://example.com" });

    expect(globalThis.fetch).toHaveBeenCalledTimes(2);
    expect(response.result.trust_score).toBe(70);
  });
});

describe("background.js — rate limiting", () => {
  it("stops calling the API once the per-minute budget is exhausted", async () => {
    globalThis.fetch.mockResolvedValue(jsonResponse(201, safeResult()));
    const max = globalThis.CyberShield.RATE_LIMIT_MAX_REQUESTS;

    for (let i = 0; i < max; i++) {
      await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: `https://example.com/${i}` });
    }
    expect(globalThis.fetch).toHaveBeenCalledTimes(max);

    const response = await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://example.com/one-too-many" });
    expect(globalThis.fetch).toHaveBeenCalledTimes(max); // no new call was made
    expect(response.result).toBeNull();
  });
});

describe("background.js — retry strategy", () => {
  it("retries a failed scan up to RETRY_MAX_ATTEMPTS times before giving up", async () => {
    vi.useFakeTimers();
    try {
      globalThis.fetch.mockResolvedValue(jsonResponse(500, { error: "Internal server error." }));
      const responsePromise = sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://flaky.example.com" });
      await vi.runAllTimersAsync();
      const response = await responsePromise;
      expect(globalThis.fetch).toHaveBeenCalledTimes(globalThis.CyberShield.RETRY_MAX_ATTEMPTS);
      expect(response.result).toBeNull();
    } finally {
      vi.useRealTimers();
    }
  });

  it("does not retry on a 401 (not signed in) or 422 (validation) error", async () => {
    globalThis.fetch.mockResolvedValue(jsonResponse(401, { error: "Authentication required." }));
    await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://example.com" });
    // 1 original call; the 401-retry-with-refresh logic in api-client itself
    // adds one refresh attempt, but scanWithRetry must not loop on top of that.
    expect(globalThis.fetch.mock.calls.length).toBeLessThanOrEqual(2);
  });
});

describe("background.js — graceful failure handling", () => {
  it("records a failed-scan stat and surfaces an error instead of throwing", async () => {
    globalThis.fetch.mockResolvedValue(jsonResponse(500, { error: "boom" }));
    const response = await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://example.com" });
    expect(response.ok).toBe(true); // the message channel itself never breaks
    expect(response.result).toBeNull();
    const stats = await globalThis.CyberShield.storage.getStats();
    expect(stats.failedScans).toBe(1);
  });
});
