import { describe, it, expect, beforeEach, vi } from "vitest";
import { createFakeChrome } from "./helpers/fake-chrome.js";
import { loadSharedScripts } from "./helpers/load-scripts.js";

function jsonResponse(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  };
}

const settings = {
  apiBaseUrl: "http://localhost:5000/api/v1",
  dashboardBaseUrl: "http://localhost:5173",
  privacyMode: false,
};

beforeEach(() => {
  delete globalThis.CyberShield;
  delete globalThis.browser;
  globalThis.chrome = createFakeChrome();
  loadSharedScripts();
  globalThis.fetch = vi.fn();
});

describe("api-client.js — request()", () => {
  it("sends credentials:'include' and no CSRF header on GET requests", async () => {
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(200, { user: { id: "1" } }));
    await globalThis.CyberShield.api.request("/users/me", { settings });

    const [url, options] = globalThis.fetch.mock.calls[0];
    expect(url).toBe("http://localhost:5000/api/v1/users/me");
    expect(options.credentials).toBe("include");
    expect(options.headers["X-CSRF-TOKEN"]).toBeUndefined();
  });

  it("attaches X-CSRF-TOKEN from the csrf_access_token cookie on mutating requests", async () => {
    globalThis.chrome.cookies.get.mockImplementation(async ({ name }) =>
      name === "csrf_access_token" ? { value: "access-csrf-value" } : null
    );
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(200, { trust_score: 90, risk: "Safe" }));

    await globalThis.CyberShield.api.request("/url/scan", { method: "POST", body: { url: "https://example.com" }, settings });

    const [, options] = globalThis.fetch.mock.calls[0];
    expect(options.headers["X-CSRF-TOKEN"]).toBe("access-csrf-value");
    expect(JSON.parse(options.body)).toEqual({ url: "https://example.com" });
  });

  it("uses the csrf_refresh_token cookie (not csrf_access_token) for /auth/refresh", async () => {
    globalThis.chrome.cookies.get.mockImplementation(async ({ name }) =>
      name === "csrf_refresh_token" ? { value: "refresh-csrf-value" } : { value: "wrong-cookie" }
    );
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(200, { message: "Token refreshed." }));

    await globalThis.CyberShield.api.refreshAccessToken(settings);

    const [, options] = globalThis.fetch.mock.calls[0];
    expect(options.headers["X-CSRF-TOKEN"]).toBe("refresh-csrf-value");
  });

  it("on a 401, refreshes the access token once and retries the original request", async () => {
    globalThis.fetch
      .mockResolvedValueOnce(jsonResponse(401, { error: "Token has expired." })) // original attempt
      .mockResolvedValueOnce(jsonResponse(200, { message: "Token refreshed." })) // refresh call
      .mockResolvedValueOnce(jsonResponse(200, { user: { id: "1" } })); // retried original request

    const result = await globalThis.CyberShield.api.request("/users/me", { settings });

    expect(globalThis.fetch).toHaveBeenCalledTimes(3);
    expect(result).toEqual({ user: { id: "1" } });
  });

  it("throws a 401 ApiError if the refresh itself fails", async () => {
    globalThis.fetch
      .mockResolvedValueOnce(jsonResponse(401, { error: "expired" }))
      .mockResolvedValueOnce(jsonResponse(401, { error: "refresh also failed" }));

    await expect(globalThis.CyberShield.api.request("/users/me", { settings })).rejects.toMatchObject({
      name: "ApiError",
      status: 401,
    });
  });

  it("wraps a network failure as a status-0 ApiError", async () => {
    globalThis.fetch.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    await expect(globalThis.CyberShield.api.request("/users/me", { settings })).rejects.toMatchObject({
      name: "ApiError",
      status: 0,
    });
  });

  it("surfaces the backend's error message and details on a non-2xx response", async () => {
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(422, { error: "Validation failed.", details: { url: ["Required."] } }));
    await expect(globalThis.CyberShield.api.request("/url/scan", { method: "POST", body: {}, settings })).rejects.toMatchObject({
      status: 422,
      message: "Validation failed.",
      details: { url: ["Required."] },
    });
  });
});

describe("api-client.js — scanUrl()", () => {
  it("calls /url/scan by default (privacyMode off)", async () => {
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(201, { trust_score: 80, risk: "Low Risk" }));
    await globalThis.CyberShield.api.scanUrl("https://example.com", { ...settings, privacyMode: false });
    expect(globalThis.fetch.mock.calls[0][0]).toContain("/url/scan");
  });

  it("calls /extension/scan when privacyMode is on", async () => {
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(200, { trust_score: 80, risk: "Low Risk", persisted: false }));
    await globalThis.CyberShield.api.scanUrl("https://example.com", { ...settings, privacyMode: true });
    expect(globalThis.fetch.mock.calls[0][0]).toContain("/extension/scan");
  });

  it("tags every scan request with X-CyberShield-Client so the backend can record its source (Phase 7)", async () => {
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(201, { trust_score: 80, risk: "Low Risk" }));
    await globalThis.CyberShield.api.scanUrl("https://example.com", { ...settings, privacyMode: false });
    const [, options] = globalThis.fetch.mock.calls[0];
    expect(options.headers["X-CyberShield-Client"]).toBe("extension");
  });
});

describe("api-client.js — checkAuth()", () => {
  it("returns true when /users/me succeeds", async () => {
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(200, { user: { id: "1" } }));
    expect(await globalThis.CyberShield.api.checkAuth(settings)).toBe(true);
  });

  it("returns false when /users/me fails (not logged in)", async () => {
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(401, { error: "Authentication required." }));
    globalThis.fetch.mockResolvedValueOnce(jsonResponse(401, { error: "Authentication required." }));
    expect(await globalThis.CyberShield.api.checkAuth(settings)).toBe(false);
  });
});
