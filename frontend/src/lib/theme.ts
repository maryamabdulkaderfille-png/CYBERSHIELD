import type { Theme } from "@/types/settings";

/** Resolves the persisted theme preference to an actual light/dark value and
 * stamps it on <html> as data-theme, which index.css keys off of for the
 * shared visual primitives (page background, glass-card, input-field,
 * btn-secondary). CyberShield's existing screens (Phases 1-4) were built
 * against a single fixed dark palette with colors hardcoded per-component,
 * so a full light-mode re-skin of every already-built page is out of scope
 * here — this wires the setting up for real (persisted, applied, responsive
 * to OS preference) at the shared-primitive level without redesigning any
 * completed screen.
 */
export function applyTheme(theme: Theme): void {
  const resolved = theme === "system" ? (prefersDark() ? "dark" : "light") : theme;
  document.documentElement.dataset.theme = resolved;
}

function prefersDark(): boolean {
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? true;
}

let systemListenerAttached = false;

export function watchSystemTheme(getCurrentTheme: () => Theme): void {
  if (systemListenerAttached || !window.matchMedia) return;
  systemListenerAttached = true;
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if (getCurrentTheme() === "system") applyTheme("system");
  });
}
