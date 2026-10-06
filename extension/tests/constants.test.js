import { describe, it, expect, beforeEach } from "vitest";
import { createFakeChrome } from "./helpers/fake-chrome.js";
import { loadScript } from "./helpers/load-scripts.js";

beforeEach(() => {
  delete globalThis.CyberShield;
  delete globalThis.browser;
  globalThis.chrome = createFakeChrome();
  loadScript("src/shared/browser-api.js");
  loadScript("src/shared/constants.js");
});

describe("constants.js", () => {
  it("defines all four risk levels consistently across maps", () => {
    const { RISK_LEVELS, RISK_COLORS, RISK_EMOJI } = globalThis.CyberShield;
    const levels = Object.values(RISK_LEVELS);
    expect(levels).toEqual(["Safe", "Low Risk", "Suspicious", "Dangerous"]);
    for (const level of levels) {
      expect(RISK_COLORS[level]).toMatch(/^#[0-9a-f]{6}$/i);
      expect(RISK_EMOJI[level]).toBeTruthy();
    }
  });

  it("default danger threshold matches the backend's Dangerous cutoff (score < 40)", () => {
    expect(globalThis.CyberShield.DEFAULT_SETTINGS.dangerThreshold).toBe(39);
  });

  it("default settings has every option the options page renders", () => {
    const settings = globalThis.CyberShield.DEFAULT_SETTINGS;
    for (const key of [
      "protectionEnabled",
      "autoScan",
      "notifications",
      "dangerThreshold",
      "theme",
      "apiBaseUrl",
      "dashboardBaseUrl",
      "privacyMode",
      "statisticsCollection",
    ]) {
      expect(settings).toHaveProperty(key);
    }
  });

  it("SKIPPED_URL_PATTERN matches internal browser pages but not http(s)", () => {
    const { SKIPPED_URL_PATTERN } = globalThis.CyberShield;
    expect(SKIPPED_URL_PATTERN.test("chrome://extensions")).toBe(true);
    expect(SKIPPED_URL_PATTERN.test("chrome-extension://abc/popup.html")).toBe(true);
    expect(SKIPPED_URL_PATTERN.test("about:blank")).toBe(true);
    expect(SKIPPED_URL_PATTERN.test("https://example.com")).toBe(false);
    expect(SKIPPED_URL_PATTERN.test("http://example.com")).toBe(false);
  });

  it("browser-api shim resolves to chrome when `browser` is undefined", () => {
    expect(globalThis.CyberShield.browserAPI).toBe(globalThis.chrome);
    expect(globalThis.CyberShield.isFirefox).toBe(false);
  });

  it("browser-api shim prefers `browser` when present (Firefox architecture readiness)", () => {
    delete globalThis.CyberShield;
    globalThis.browser = { fakeFirefoxNamespace: true };
    loadScript("src/shared/browser-api.js");
    expect(globalThis.CyberShield.browserAPI).toBe(globalThis.browser);
    expect(globalThis.CyberShield.isFirefox).toBe(true);
  });
});
