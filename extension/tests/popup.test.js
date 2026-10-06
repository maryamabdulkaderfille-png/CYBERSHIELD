import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { createFakeChrome } from "./helpers/fake-chrome.js";
import { loadSharedScripts, loadScript } from "./helpers/load-scripts.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function jsonResponse(status, body) {
  return { ok: status >= 200 && status < 300, status, json: async () => body };
}

const popupHtml = fs.readFileSync(path.join(__dirname, "..", "src", "popup", "popup.html"), "utf8");

function extractBody(html) {
  const match = html.match(/<body>([\s\S]*)<\/body>/);
  return match[1];
}

beforeEach(() => {
  delete globalThis.CyberShield;
  delete globalThis.browser;
  document.documentElement.innerHTML = `<head></head><body>${extractBody(popupHtml)}</body>`;
  globalThis.chrome = createFakeChrome();
  globalThis.fetch = vi.fn();
  // jsdom doesn't implement matchMedia; popup.js calls it when theme is
  // "system" (the default), so tests need a stub, same as the real app's
  // matchMedia("(prefers-color-scheme: dark)") usage.
  window.matchMedia = vi.fn().mockReturnValue({ matches: false, addEventListener() {}, removeEventListener() {} });
  loadSharedScripts();
});

function loadPopupScript() {
  loadScript("src/popup/popup.js");
}

describe("popup.js — states", () => {
  it("shows the result state with the correct score, risk badge, and reasons", async () => {
    globalThis.chrome.tabs.query.mockResolvedValue([{ id: 1, url: "https://example.com/login" }]);
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(200, { user: { id: "1" } })); // checkAuth
    globalThis.chrome.runtime.sendMessage.mockImplementation(async (message) => {
      if (message.type === "GET_TAB_STATE") return { ok: true, state: null };
      if (message.type === "GET_OR_SCAN_VERDICT") {
        return {
          ok: true,
          result: {
            trust_score: 62,
            risk: "Suspicious",
            reasons: ["Domain registered recently."],
            recommendations: ["Proceed with caution."],
            scan_date: "2026-01-01T12:00:00Z",
          },
          isBlocking: false,
        };
      }
      return { ok: true };
    });

    loadPopupScript();

    await vi.waitFor(() => {
      expect(document.getElementById("stateResult").classList.contains("state-hidden")).toBe(false);
    });

    expect(document.getElementById("siteHost").textContent).toBe("example.com");
    expect(document.getElementById("scoreValue").textContent).toBe("62");
    expect(document.getElementById("riskBadge").textContent).toBe("Suspicious");
    expect(document.getElementById("riskBadge").className).toContain("risk-suspicious");
    expect(document.getElementById("reasonsList").children.length).toBe(1);
  });

  it("shows the signed-out state when the user isn't authenticated", async () => {
    globalThis.chrome.tabs.query.mockResolvedValue([{ id: 1, url: "https://example.com" }]);
    globalThis.fetch.mockResolvedValue(jsonResponse(401, { error: "Authentication required." }));

    loadPopupScript();

    await vi.waitFor(() => {
      expect(document.getElementById("stateSignedOut").classList.contains("state-hidden")).toBe(false);
    });
  });

  it("shows the unscannable state for a chrome:// page", async () => {
    globalThis.chrome.tabs.query.mockResolvedValue([{ id: 1, url: "chrome://extensions" }]);

    loadPopupScript();

    await vi.waitFor(() => {
      expect(document.getElementById("stateUnscannable").classList.contains("state-hidden")).toBe(false);
    });
    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it("shows the error state when the scan fails", async () => {
    globalThis.chrome.tabs.query.mockResolvedValue([{ id: 1, url: "https://example.com" }]);
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(200, { user: { id: "1" } }));
    globalThis.chrome.runtime.sendMessage.mockImplementation(async (message) => {
      if (message.type === "GET_TAB_STATE") return { ok: true, state: null };
      if (message.type === "GET_OR_SCAN_VERDICT") return { ok: true, result: null, error: "Rate limit reached — skipping this scan." };
      return { ok: true };
    });

    loadPopupScript();

    await vi.waitFor(() => {
      expect(document.getElementById("stateError").classList.contains("state-hidden")).toBe(false);
    });
    expect(document.getElementById("errorMessage").textContent).toBe("Rate limit reached — skipping this scan.");
  });
});

describe("popup.js — quick actions", () => {
  async function renderResultState() {
    globalThis.chrome.tabs.query.mockResolvedValue([{ id: 1, url: "https://example.com" }]);
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(200, { user: { id: "1" } }));
    globalThis.chrome.runtime.sendMessage.mockImplementation(async (message) => {
      if (message.type === "GET_TAB_STATE") return { ok: true, state: null };
      if (message.type === "GET_OR_SCAN_VERDICT") {
        return { ok: true, result: { id: 99, trust_score: 12, risk: "Dangerous", reasons: [], recommendations: [] }, isBlocking: true };
      }
      if (message.type === "RESCAN") {
        return { ok: true, result: { id: 99, trust_score: 40, risk: "Suspicious", reasons: [], recommendations: [] }, isBlocking: false };
      }
      return { ok: true };
    });
    loadPopupScript();
    await vi.waitFor(() => {
      expect(document.getElementById("stateResult").classList.contains("state-hidden")).toBe(false);
    });
  }

  it("Dashboard button opens the configured dashboard URL", async () => {
    await renderResultState();
    document.getElementById("btnDashboard").click();
    await vi.waitFor(() => expect(globalThis.chrome.tabs.create).toHaveBeenCalled());
    expect(globalThis.chrome.tabs.create).toHaveBeenCalledWith({ url: "http://localhost:5173" });
  });

  it("Report button opens the report page for a persisted scan id", async () => {
    await renderResultState();
    document.getElementById("btnReport").click();
    await vi.waitFor(() => expect(globalThis.chrome.tabs.create).toHaveBeenCalled());
    expect(globalThis.chrome.tabs.create).toHaveBeenCalledWith({ url: "http://localhost:5173/dashboard/reports/url/99" });
  });

  it("Settings button opens the extension's options page", async () => {
    await renderResultState();
    document.getElementById("btnSettings").click();
    expect(globalThis.chrome.runtime.openOptionsPage).toHaveBeenCalled();
  });

  it("Rescan button re-renders with the fresh result", async () => {
    await renderResultState();
    document.getElementById("btnRescan").click();
    await vi.waitFor(() => {
      expect(document.getElementById("scoreValue").textContent).toBe("40");
    });
    expect(document.getElementById("riskBadge").textContent).toBe("Suspicious");
  });
});

describe("popup.js — blocked state (Personal Block List)", () => {
  function blockedEntry(overrides = {}) {
    return {
      id: 7,
      domain: "evil-example.com",
      trust_score: 4,
      reason: "Domain appears on the CyberShield blacklist.",
      ...overrides,
    };
  }

  async function renderBlockedState(unblockHandler) {
    globalThis.chrome.tabs.query.mockResolvedValue([{ id: 1, url: "https://evil-example.com" }]);
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(200, { user: { id: "1" } }));
    globalThis.chrome.runtime.sendMessage.mockImplementation(async (message) => {
      if (message.type === "GET_TAB_STATE") return { ok: true, state: null };
      if (message.type === "GET_OR_SCAN_VERDICT") {
        return { ok: true, result: null, isBlocking: false, hardBlocked: true, blockedEntry: blockedEntry() };
      }
      if (message.type === "UNBLOCK_FROM_WARNING" && unblockHandler) return unblockHandler(message);
      return { ok: true };
    });
    loadPopupScript();
    await vi.waitFor(() => {
      expect(document.getElementById("stateBlocked").classList.contains("state-hidden")).toBe(false);
    });
  }

  it("shows the blocked state with the domain, score, and reason", async () => {
    await renderBlockedState();

    expect(document.getElementById("blockedHost").textContent).toBe("evil-example.com");
    expect(document.getElementById("blockedScore").textContent).toBe("4");
    expect(document.getElementById("blockedReason").textContent).toBe("Domain appears on the CyberShield blacklist.");
  });

  it("'Remove From Block List' reloads the tab and re-renders on success", async () => {
    await renderBlockedState(async () => ({ ok: true }));

    document.getElementById("btnUnblock").click();

    await vi.waitFor(() => {
      expect(globalThis.chrome.tabs.reload).toHaveBeenCalledWith(1);
    });
    expect(document.getElementById("unblockError").style.display).toBe("none");
  });

  it("'Remove From Block List' shows an inline error and stays on the blocked state when it fails", async () => {
    await renderBlockedState(async () => ({ ok: false, error: "Could not unblock." }));

    document.getElementById("btnUnblock").click();

    await vi.waitFor(() => {
      expect(document.getElementById("unblockError").style.display).not.toBe("none");
    });
    expect(document.getElementById("unblockError").textContent).toBe("Could not unblock.");
    expect(document.getElementById("stateBlocked").classList.contains("state-hidden")).toBe(false);
    expect(document.getElementById("btnUnblock").disabled).toBe(false);
  });
});
