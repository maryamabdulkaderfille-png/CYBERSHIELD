import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Indirect eval always runs in the current realm's global scope (whatever
// `globalThis` is for the running test file — jsdom's window in our case),
// which is what lets these plain, non-module extension scripts attach
// themselves to `globalThis.CyberShield` exactly like they do in a real
// browser, without a bundler or CommonJS wrapper.
const indirectEval = eval;

export function loadScript(relativePath) {
  const fullPath = path.join(__dirname, "..", "..", relativePath);
  const code = fs.readFileSync(fullPath, "utf8");
  indirectEval(code);
}

export function loadSharedScripts() {
  loadScript("src/shared/browser-api.js");
  loadScript("src/shared/constants.js");
  loadScript("src/shared/storage.js");
  loadScript("src/shared/api-client.js");
}
