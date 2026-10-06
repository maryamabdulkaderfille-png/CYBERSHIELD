/**
 * Cross-browser WebExtension API shim.
 *
 * Chrome/Edge (Manifest V3) expose `chrome.*` and, since Chrome 88, return a
 * Promise from most async APIs when the callback argument is omitted.
 * Firefox exposes a `browser.*` namespace that is Promise-based natively.
 * Aliasing one to the other here means every other file in this extension
 * can call `CyberShield.browserAPI.storage.local.get(...)` etc. and just
 * work on both, without a bundled polyfill library — the architecture Part 1
 * asks for ("prepare architecture so Firefox support can be added later")
 * without adding a build step.
 */
(function (global) {
  const CyberShield = global.CyberShield || (global.CyberShield = {});
  CyberShield.browserAPI = typeof browser !== "undefined" ? browser : chrome;
  CyberShield.isFirefox = typeof browser !== "undefined";
})(typeof self !== "undefined" ? self : this);
