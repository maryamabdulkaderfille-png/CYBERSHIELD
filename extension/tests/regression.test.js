import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it, expect, beforeEach } from "vitest";
import { createFakeChrome } from "./helpers/fake-chrome.js";
import { loadSharedScripts } from "./helpers/load-scripts.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "manifest.json"), "utf8"));

describe("regression — manifest.json", () => {
  it("is a valid Manifest V3 extension manifest with the required surfaces", () => {
    expect(manifest.manifest_version).toBe(3);
    expect(manifest.background.service_worker).toBe("src/background/background.js");
    expect(manifest.action.default_popup).toBe("src/popup/popup.html");
    expect(manifest.options_ui.page).toBe("src/options/options.html");
    expect(manifest.content_scripts).toHaveLength(1);
    expect(manifest.content_scripts[0].matches).toEqual(["http://*/*", "https://*/*"]);
  });

  it("requests only the permissions the code actually uses", () => {
    // A guard against permission creep — every entry here must be
    // justifiable by a specific feature (see README's permissions table).
    expect(manifest.permissions.sort()).toEqual(
      ["storage", "notifications", "alarms", "webNavigation", "tabs", "cookies"].sort()
    );
    expect(manifest.permissions).not.toContain("scripting"); // static content_scripts only
    expect(manifest.permissions).not.toContain("<all_urls>"); // host_permissions used instead, scoped to http(s)
  });

  it("every file referenced by the manifest actually exists", () => {
    const root = path.join(__dirname, "..");
    const referenced = [
      manifest.background.service_worker,
      manifest.action.default_popup,
      manifest.options_ui.page,
      ...manifest.content_scripts[0].js,
      ...Object.values(manifest.icons),
    ];
    for (const relativePath of referenced) {
      expect(fs.existsSync(path.join(root, relativePath)), `${relativePath} should exist`).toBe(true);
    }
  });
});

describe("regression — shared module public surface", () => {
  beforeEach(() => {
    delete globalThis.CyberShield;
    delete globalThis.browser;
    globalThis.chrome = createFakeChrome();
    loadSharedScripts();
  });

  it("CyberShield.api exposes the expected functions", () => {
    expect(globalThis.CyberShield.api).toHaveProperty("request");
    expect(globalThis.CyberShield.api).toHaveProperty("checkAuth");
    expect(globalThis.CyberShield.api).toHaveProperty("scanUrl");
    expect(globalThis.CyberShield.api).toHaveProperty("refreshAccessToken");
  });

  it("CyberShield.storage exposes the expected functions", () => {
    for (const fn of [
      "getSettings",
      "setSettings",
      "getCache",
      "setCache",
      "getCachedResult",
      "setCachedResult",
      "pruneExpiredCache",
      "getStats",
      "recordStat",
      "getSessionOverrides",
      "addSessionOverride",
    ]) {
      expect(globalThis.CyberShield.storage).toHaveProperty(fn);
      expect(typeof globalThis.CyberShield.storage[fn]).toBe("function");
    }
  });

  it("ApiError carries a status and optional details", () => {
    const err = new globalThis.CyberShield.ApiError("boom", 500, { field: ["bad"] });
    expect(err.message).toBe("boom");
    expect(err.status).toBe(500);
    expect(err.details).toEqual({ field: ["bad"] });
    expect(err).toBeInstanceOf(Error);
  });
});
