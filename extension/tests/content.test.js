import { describe, it, expect, beforeEach, vi } from "vitest";
import { createFakeChrome } from "./helpers/fake-chrome.js";
import { loadSharedScripts, loadScript } from "./helpers/load-scripts.js";

function dangerousResult(overrides = {}) {
  return {
    id: 42,
    trust_score: 8,
    risk: "Dangerous",
    reasons: ["Domain appears on the CyberShield blacklist."],
    recommendations: ["Do not enter any personal information."],
    ...overrides,
  };
}

function mockSendMessage(handlers) {
  globalThis.chrome.runtime.sendMessage.mockImplementation(async (message) => {
    const handler = handlers[message.type];
    return handler ? handler(message) : { ok: true };
  });
}

function blockedEntry(overrides = {}) {
  return {
    id: 7,
    domain: "evil-example.com",
    trust_score: 4,
    risk_level: "Dangerous",
    reason: "Domain appears on the CyberShield blacklist.",
    scanner_type: "url",
    scan_id: 55,
    ...overrides,
  };
}

// content.js deliberately uses a *closed* shadow root (see content.js's
// comments) so the host page's own JS can never reach in via
// element.shadowRoot — that's a real security property, not a test
// inconvenience, so we don't weaken it to `open` just to make assertions
// easier. Instead, capture the root at creation time by wrapping
// attachShadow itself: this observes what content.js legitimately holds a
// reference to, the same way the content script itself does, without
// reproducing the "reach in from outside after the fact" that `closed`
// exists to block.
let capturedShadowRoot = null;
const nativeAttachShadow = Element.prototype.attachShadow;

beforeEach(() => {
  delete globalThis.CyberShield;
  delete globalThis.browser;
  document.documentElement.innerHTML = "<head></head><body></body>";
  globalThis.chrome = createFakeChrome();
  loadSharedScripts();
  loadScript("src/content/warning-styles.js");

  capturedShadowRoot = null;
  Element.prototype.attachShadow = function (init) {
    const root = nativeAttachShadow.call(this, init);
    capturedShadowRoot = root;
    return root;
  };
});

function loadContentScript() {
  loadScript("src/content/content.js");
}

describe("content.js — warning overlay", () => {
  it("renders the full-page warning overlay when the verdict is blocking", async () => {
    mockSendMessage({
      GET_SESSION_OVERRIDES: async () => ({ ok: true, overrides: {} }),
      GET_OR_SCAN_VERDICT: async () => ({ ok: true, result: dangerousResult(), isBlocking: true }),
    });

    loadContentScript();

    await vi.waitFor(() => {
      expect(document.getElementById("cybershield-warning-host")).toBeTruthy();
    });

    const host = document.getElementById("cybershield-warning-host");
    expect(capturedShadowRoot).toBeTruthy();
    expect(capturedShadowRoot.querySelector(".cs-card")).toBeTruthy();
    expect(capturedShadowRoot.querySelector('[data-action="go-back"]')).toBeTruthy();
    expect(capturedShadowRoot.querySelector('[data-action="continue"]')).toBeTruthy();
    expect(capturedShadowRoot.querySelector('[data-action="view-report"]')).toBeTruthy();
  });

  it("does not render an overlay for a Safe verdict", async () => {
    mockSendMessage({
      GET_SESSION_OVERRIDES: async () => ({ ok: true, overrides: {} }),
      GET_OR_SCAN_VERDICT: async () => ({ ok: true, result: { trust_score: 95, risk: "Safe" }, isBlocking: false }),
    });

    loadContentScript();
    await vi.waitFor(() => {
      expect(globalThis.chrome.runtime.sendMessage).toHaveBeenCalled();
    });
    expect(document.getElementById("cybershield-warning-host")).toBeNull();
  });

  it("skips scanning entirely when this host has a 'continue anyway' session override", async () => {
    mockSendMessage({
      GET_SESSION_OVERRIDES: async () => ({ ok: true, overrides: { localhost: Date.now() } }),
    });

    loadContentScript();
    await vi.waitFor(() => {
      expect(globalThis.chrome.runtime.sendMessage).toHaveBeenCalledWith(
        expect.objectContaining({ type: "GET_SESSION_OVERRIDES" })
      );
    });

    const calledScan = globalThis.chrome.runtime.sendMessage.mock.calls.some((call) => call[0].type === "GET_OR_SCAN_VERDICT");
    expect(calledScan).toBe(false);
    expect(document.getElementById("cybershield-warning-host")).toBeNull();
  });

  it("'Continue Anyway' removes the overlay and records a session override", async () => {
    mockSendMessage({
      GET_SESSION_OVERRIDES: async () => ({ ok: true, overrides: {} }),
      GET_OR_SCAN_VERDICT: async () => ({ ok: true, result: dangerousResult(), isBlocking: true }),
      CONTINUE_ANYWAY: async () => ({ ok: true }),
    });

    loadContentScript();
    await vi.waitFor(() => expect(document.getElementById("cybershield-warning-host")).toBeTruthy());

    const host = document.getElementById("cybershield-warning-host");
    capturedShadowRoot.querySelector('[data-action="continue"]').click();

    await vi.waitFor(() => expect(document.getElementById("cybershield-warning-host")).toBeNull());

    const continueCall = globalThis.chrome.runtime.sendMessage.mock.calls.find((call) => call[0].type === "CONTINUE_ANYWAY");
    expect(continueCall).toBeTruthy();
  });

  it("'Go Back' calls history.back() when there is history to go back to", async () => {
    mockSendMessage({
      GET_SESSION_OVERRIDES: async () => ({ ok: true, overrides: {} }),
      GET_OR_SCAN_VERDICT: async () => ({ ok: true, result: dangerousResult(), isBlocking: true }),
    });
    const backSpy = vi.spyOn(window.history, "back").mockImplementation(() => {});
    Object.defineProperty(window.history, "length", { value: 2, configurable: true });

    loadContentScript();
    await vi.waitFor(() => expect(document.getElementById("cybershield-warning-host")).toBeTruthy());

    capturedShadowRoot.querySelector('[data-action="go-back"]').click();
    expect(backSpy).toHaveBeenCalled();
  });

  it("updates the overlay live when the background pushes VERDICT_UPDATED after a rescan", async () => {
    mockSendMessage({
      GET_SESSION_OVERRIDES: async () => ({ ok: true, overrides: {} }),
      GET_OR_SCAN_VERDICT: async () => ({ ok: true, result: dangerousResult(), isBlocking: true }),
    });

    loadContentScript();
    await vi.waitFor(() => expect(document.getElementById("cybershield-warning-host")).toBeTruthy());

    const listener = globalThis.chrome.__listeners.runtimeOnMessage[0];
    listener({ type: "VERDICT_UPDATED", url: location.href, result: { trust_score: 95, risk: "Safe" }, isBlocking: false });

    await vi.waitFor(() => expect(document.getElementById("cybershield-warning-host")).toBeNull());
  });
});

describe("content.js — hard block overlay (Personal Block List)", () => {
  // jsdom's Location#reload isn't a configurable own property, so
  // vi.spyOn(window.location, "reload") fails with "Cannot redefine
  // property". Replacing window.location itself (an accessor jsdom does
  // allow redefining) with a plain-object copy plus a spy is the standard
  // workaround.
  let reloadSpy;
  beforeEach(() => {
    reloadSpy = vi.fn();
    const currentLocation = window.location;
    Object.defineProperty(window, "location", {
      configurable: true,
      value: { ...currentLocation, reload: reloadSpy },
    });
  });

  it("renders the hard-block overlay (no 'Continue Anyway' button) when the host is on the block list", async () => {
    mockSendMessage({
      GET_SESSION_OVERRIDES: async () => ({ ok: true, overrides: {} }),
      GET_OR_SCAN_VERDICT: async () => ({ ok: true, result: null, isBlocking: false, hardBlocked: true, blockedEntry: blockedEntry() }),
    });

    loadContentScript();

    await vi.waitFor(() => {
      expect(document.getElementById("cybershield-warning-host")).toBeTruthy();
    });

    expect(capturedShadowRoot.querySelector('[data-action="go-back"]')).toBeTruthy();
    expect(capturedShadowRoot.querySelector('[data-action="view-details"]')).toBeTruthy();
    expect(capturedShadowRoot.querySelector('[data-action="remove-block"]')).toBeTruthy();
    expect(capturedShadowRoot.querySelector('[data-action="continue"]')).toBeNull();
    expect(capturedShadowRoot.querySelector(".cs-value").textContent).toBe(location.host);
  });

  it("'Remove From Block List' removes the overlay and reloads the page on success", async () => {
    mockSendMessage({
      GET_SESSION_OVERRIDES: async () => ({ ok: true, overrides: {} }),
      GET_OR_SCAN_VERDICT: async () => ({ ok: true, result: null, isBlocking: false, hardBlocked: true, blockedEntry: blockedEntry() }),
      UNBLOCK_FROM_WARNING: async () => ({ ok: true }),
    });

    loadContentScript();
    await vi.waitFor(() => expect(document.getElementById("cybershield-warning-host")).toBeTruthy());

    capturedShadowRoot.querySelector('[data-action="remove-block"]').click();

    await vi.waitFor(() => expect(document.getElementById("cybershield-warning-host")).toBeNull());
    expect(reloadSpy).toHaveBeenCalled();
  });

  it("'Remove From Block List' shows an inline error and keeps the overlay when the unblock call fails", async () => {
    mockSendMessage({
      GET_SESSION_OVERRIDES: async () => ({ ok: true, overrides: {} }),
      GET_OR_SCAN_VERDICT: async () => ({ ok: true, result: null, isBlocking: false, hardBlocked: true, blockedEntry: blockedEntry() }),
      UNBLOCK_FROM_WARNING: async () => ({ ok: false, error: "Could not unblock." }),
    });

    loadContentScript();
    await vi.waitFor(() => expect(document.getElementById("cybershield-warning-host")).toBeTruthy());

    capturedShadowRoot.querySelector('[data-action="remove-block"]').click();

    await vi.waitFor(() => {
      const errorEl = capturedShadowRoot.querySelector('[data-role="unblock-error"]');
      expect(errorEl.style.display).not.toBe("none");
      expect(errorEl.textContent).toBe("Could not unblock.");
    });
    expect(document.getElementById("cybershield-warning-host")).toBeTruthy();
    expect(reloadSpy).not.toHaveBeenCalled();
  });
});
