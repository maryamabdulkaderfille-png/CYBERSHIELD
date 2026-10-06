import { describe, it, expect, beforeEach, vi } from "vitest";
import { createFakeChrome } from "./helpers/fake-chrome.js";
import { loadSharedScripts, loadScript } from "./helpers/load-scripts.js";

function jsonResponse(status, body) {
  return { ok: status >= 200 && status < 300, status, json: async () => body };
}

function dangerousResult(overrides = {}) {
  return {
    id: 42,
    trust_score: 10,
    risk: "Dangerous",
    reasons: ["Blacklisted"],
    recommendations: ["Do not proceed."],
    rules: [],
    ...overrides,
  };
}

function suspiciousResult(overrides = {}) {
  return { id: 43, trust_score: 55, risk: "Suspicious", reasons: [], recommendations: [], rules: [], ...overrides };
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

describe("Phase 9 — hard block enforcement", () => {
  it("hard-blocks a synced domain without calling the scan API at all", async () => {
    await globalThis.CyberShield.storage.setProtectionSync({
      blockedDomains: [{ id: 7, domain: "evil.example", trust_score: 5, risk_level: "Dangerous", reason: "Fake bank" }],
      protectionMode: "warn_only",
    });
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(201, { message: "Recorded." })); // extension-blocked-event

    const response = await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://evil.example/login" });

    expect(response.hardBlocked).toBe(true);
    expect(response.blockedEntry.domain).toBe("evil.example");
    expect(response.result).toBeNull();
    // The extension-blocked-event report is intentionally fire-and-forget
    // (never awaited before sendResponse) — wait for it rather than
    // asserting synchronously.
    await vi.waitFor(() => expect(globalThis.fetch).toHaveBeenCalledTimes(1));
    expect(globalThis.fetch.mock.calls[0][0]).toContain("/protection/extension-blocked-event");
  });

  it("matches a subdomain of a blocked registrable domain", async () => {
    await globalThis.CyberShield.storage.setProtectionSync({
      blockedDomains: [{ id: 7, domain: "evil.example", trust_score: 5, risk_level: "Dangerous", reason: null }],
      protectionMode: "warn_only",
    });
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(201, { message: "Recorded." }));

    const response = await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://login.evil.example/verify" });
    expect(response.hardBlocked).toBe(true);
  });

  it("never hard-blocks localhost even if it were somehow in the synced list", async () => {
    await globalThis.CyberShield.storage.setProtectionSync({
      blockedDomains: [{ id: 1, domain: "localhost", trust_score: 5, risk_level: "Dangerous", reason: null }],
      protectionMode: "warn_only",
    });
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(201, { trust_score: 95, risk: "Safe", reasons: [], recommendations: [], rules: [] }));

    const response = await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "http://localhost:5173/" });
    expect(response.hardBlocked).toBe(false);
  });

  it("never hard-blocks the configured dashboard origin", async () => {
    await globalThis.CyberShield.storage.setProtectionSync({
      blockedDomains: [{ id: 1, domain: "localhost", trust_score: 5, risk_level: "Dangerous", reason: null }],
      protectionMode: "warn_only",
    });
    // dashboardBaseUrl defaults to http://localhost:5173 — same host as above,
    // covered by the localhost literal check either way, so use 127.0.0.1
    // pointed at by settings instead to exercise the dashboard-host branch.
    await globalThis.CyberShield.storage.setSettings({ dashboardBaseUrl: "http://cybershield.example" });
    await globalThis.CyberShield.storage.setProtectionSync({
      blockedDomains: [{ id: 2, domain: "cybershield.example", trust_score: 5, risk_level: "Dangerous", reason: null }],
      protectionMode: "warn_only",
    });
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(201, { trust_score: 95, risk: "Safe", reasons: [], recommendations: [], rules: [] }));

    const response = await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "http://cybershield.example/dashboard" });
    expect(response.hardBlocked).toBe(false);
  });

  it("GET_TAB_STATE reflects a hard-blocked tab after a navigation event", async () => {
    await globalThis.CyberShield.storage.setProtectionSync({
      blockedDomains: [{ id: 7, domain: "evil.example", trust_score: 5, risk_level: "Dangerous", reason: null }],
      protectionMode: "warn_only",
    });
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(201, { message: "Recorded." }));

    // The onCommitted listener calls handleNavigation without awaiting it
    // (matching the pre-existing getOrScanVerdict call it replaced), so wait
    // for tab state to actually land rather than assuming it's synchronous.
    const onCommitted = fakeChrome.__listeners.webNavigationOnCommitted[0];
    onCommitted({ frameId: 0, tabId: 1, url: "https://evil.example/login" });

    await vi.waitFor(async () => {
      const response = await sendMessage({ type: "GET_TAB_STATE", tabId: 1 });
      expect(response.state?.hardBlocked).toBe(true);
    });
    const finalResponse = await sendMessage({ type: "GET_TAB_STATE", tabId: 1 });
    expect(finalResponse.state.blockedEntry.domain).toBe("evil.example");
  });
});

describe("Phase 9 — Active Protection auto-block modes", () => {
  it("does not auto-block anything under warn_only (default)", async () => {
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(201, dangerousResult()));
    await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://newly-dangerous.example" });
    expect(globalThis.fetch).toHaveBeenCalledTimes(1); // only the scan call
  });

  it("auto-blocks a Dangerous result under auto_block_dangerous", async () => {
    await globalThis.CyberShield.storage.setProtectionSync({ blockedDomains: [], protectionMode: "auto_block_dangerous" });
    globalThis.fetch
      .mockResolvedValueOnce(jsonResponse(201, dangerousResult()))
      .mockResolvedValueOnce(jsonResponse(201, { entry: { id: 99, domain: "newly-dangerous.example", trust_score: 10, risk_level: "Dangerous", reasons: ["Blacklisted"], scanner_type: "url", scan_id: 42 } }));

    await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://newly-dangerous.example" });

    expect(globalThis.fetch).toHaveBeenCalledTimes(2);
    expect(globalThis.fetch.mock.calls[1][0]).toContain("/protection/blocklist");
    const sync = await globalThis.CyberShield.storage.getProtectionSync();
    expect(sync.blockedDomains.some((e) => e.domain === "newly-dangerous.example")).toBe(true);
  });

  it("does not auto-block a Suspicious result under auto_block_dangerous (Dangerous-only mode)", async () => {
    await globalThis.CyberShield.storage.setProtectionSync({ blockedDomains: [], protectionMode: "auto_block_dangerous" });
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(201, suspiciousResult()));

    await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://kinda-sketchy.example" });

    expect(globalThis.fetch).toHaveBeenCalledTimes(1); // only the scan call, no block call
  });

  it("auto-blocks a Suspicious result under auto_block_dangerous_suspicious", async () => {
    await globalThis.CyberShield.storage.setProtectionSync({ blockedDomains: [], protectionMode: "auto_block_dangerous_suspicious" });
    globalThis.fetch
      .mockResolvedValueOnce(jsonResponse(201, suspiciousResult()))
      .mockResolvedValueOnce(jsonResponse(201, { entry: { id: 100, domain: "kinda-sketchy.example", trust_score: 55, risk_level: "Suspicious", reasons: [], scanner_type: "url", scan_id: 43 } }));

    await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://kinda-sketchy.example" });

    expect(globalThis.fetch).toHaveBeenCalledTimes(2);
    expect(globalThis.fetch.mock.calls[1][0]).toContain("/protection/blocklist");
  });

  it("never auto-blocks the dashboard's own origin even in the strictest mode", async () => {
    await globalThis.CyberShield.storage.setSettings({ dashboardBaseUrl: "https://dangerous-but-is-cybershield.example" });
    await globalThis.CyberShield.storage.setProtectionSync({ blockedDomains: [], protectionMode: "auto_block_dangerous_suspicious" });
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(201, dangerousResult()));

    await sendMessage({ type: "GET_OR_SCAN_VERDICT", tabId: 1, url: "https://dangerous-but-is-cybershield.example/dashboard" });

    expect(globalThis.fetch).toHaveBeenCalledTimes(1); // scan only, no auto-block call
  });
});

describe("Phase 9 — Remove From Block List (from the hard-block warning page)", () => {
  it("UNBLOCK_FROM_WARNING calls the unblock API and updates the synced cache", async () => {
    await globalThis.CyberShield.storage.setProtectionSync({
      blockedDomains: [{ id: 7, domain: "evil.example", trust_score: 5, risk_level: "Dangerous", reason: null }],
      protectionMode: "warn_only",
    });
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(200, { message: "Website unblocked.", entry: { id: 7 } }));

    const response = await sendMessage({ type: "UNBLOCK_FROM_WARNING", tabId: 1, entryId: 7 });

    expect(response.ok).toBe(true);
    expect(globalThis.fetch.mock.calls[0][0]).toContain("/protection/blocklist/7");
    expect(globalThis.fetch.mock.calls[0][1].method).toBe("DELETE");
    const sync = await globalThis.CyberShield.storage.getProtectionSync();
    expect(sync.blockedDomains).toEqual([]);
  });
});
