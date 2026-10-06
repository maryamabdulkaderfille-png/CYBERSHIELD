import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { createFakeChrome } from "./helpers/fake-chrome.js";
import { loadSharedScripts, loadScript } from "./helpers/load-scripts.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const optionsHtml = fs.readFileSync(path.join(__dirname, "..", "src", "options", "options.html"), "utf8");

function extractBody(html) {
  const match = html.match(/<body>([\s\S]*)<\/body>/);
  return match[1];
}

beforeEach(() => {
  delete globalThis.CyberShield;
  delete globalThis.browser;
  document.documentElement.innerHTML = `<head></head><body>${extractBody(optionsHtml)}</body>`;
  globalThis.chrome = createFakeChrome();
  loadSharedScripts();
});

function loadOptionsScript() {
  loadScript("src/options/options.js");
}

describe("options.js — load", () => {
  it("fills the form from the current settings, including saved defaults", async () => {
    loadOptionsScript();

    await vi.waitFor(() => {
      expect(document.getElementById("apiBaseUrl").value).toBe("http://localhost:5000/api/v1");
    });
    expect(document.getElementById("dashboardBaseUrl").value).toBe("http://localhost:5173");
    expect(document.getElementById("dangerThresholdValue").textContent).toBe(
      String(document.getElementById("dangerThreshold").value)
    );
  });

  it("renders local statistics from storage", async () => {
    globalThis.chrome.__storageData.local["cybershield_stats"] = {
      totalScans: 12,
      dangerousBlocked: 3,
      suspiciousWarned: 2,
      failedScans: 1,
    };

    loadOptionsScript();

    await vi.waitFor(() => {
      expect(document.getElementById("statTotal").textContent).toBe("12");
    });
    expect(document.getElementById("statDangerous").textContent).toBe("3");
    expect(document.getElementById("statSuspicious").textContent).toBe("2");
    expect(document.getElementById("statFailed").textContent).toBe("1");
  });
});

describe("options.js — save", () => {
  it("persists a valid form to storage and shows a confirmation", async () => {
    loadOptionsScript();
    await vi.waitFor(() => expect(document.getElementById("apiBaseUrl").value).toBeTruthy());

    document.getElementById("apiBaseUrl").value = "https://api.example.com/api/v1";
    document.getElementById("dashboardBaseUrl").value = "https://app.example.com";
    document.getElementById("btnSave").click();

    await vi.waitFor(() => {
      expect(document.getElementById("saveStatus").textContent).toBe("Saved.");
    });
    const stored = globalThis.chrome.__storageData.sync["cybershield_settings"];
    expect(stored.apiBaseUrl).toBe("https://api.example.com/api/v1");
    expect(stored.dashboardBaseUrl).toBe("https://app.example.com");
  });

  it("rejects a malformed API URL without saving", async () => {
    loadOptionsScript();
    await vi.waitFor(() => expect(document.getElementById("apiBaseUrl").value).toBeTruthy());

    document.getElementById("apiBaseUrl").value = "not-a-url";
    document.getElementById("btnSave").click();

    await vi.waitFor(() => {
      expect(document.getElementById("saveStatus").textContent).toMatch(/API URL must be a valid/);
    });
    const stored = globalThis.chrome.__storageData.sync["cybershield_settings"];
    expect(stored).toBeUndefined();
  });

  it("rejects a malformed dashboard URL without saving", async () => {
    loadOptionsScript();
    await vi.waitFor(() => expect(document.getElementById("apiBaseUrl").value).toBeTruthy());

    document.getElementById("dashboardBaseUrl").value = "ftp://wrong-scheme.example.com";
    document.getElementById("btnSave").click();

    await vi.waitFor(() => {
      expect(document.getElementById("saveStatus").textContent).toMatch(/Dashboard URL must be a valid/);
    });
    const stored = globalThis.chrome.__storageData.sync["cybershield_settings"];
    expect(stored).toBeUndefined();
  });

  it("allows clearing the API URL (blank is treated as unconfigured, not invalid)", async () => {
    loadOptionsScript();
    await vi.waitFor(() => expect(document.getElementById("apiBaseUrl").value).toBeTruthy());

    document.getElementById("apiBaseUrl").value = "";
    document.getElementById("btnSave").click();

    await vi.waitFor(() => {
      expect(document.getElementById("saveStatus").textContent).toBe("Saved.");
    });
    const stored = globalThis.chrome.__storageData.sync["cybershield_settings"];
    expect(stored.apiBaseUrl).toBe("");
  });
});
