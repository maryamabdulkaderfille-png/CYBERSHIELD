# CyberShield Browser Extension

Manifest V3 extension providing real-time phishing protection, built on top
of the existing CyberShield URL Security Engine and auth system. See the
main [README.md](../README.md#phase-6-browser-extension) for the full
architecture writeup — this file is just the "how do I run/load/test it"
quick reference.

No build step: everything under `src/` is loaded by the browser exactly as
written (plain JS/HTML/CSS, no bundler).

## Load it in Chrome or Edge

1. Make sure the backend and frontend are running (`docker compose up -d`
   from the repo root) and you're logged in to CyberShield at
   `http://localhost:5173` in the same browser.
2. Go to `chrome://extensions` (or `edge://extensions`), enable
   **Developer mode**, click **Load unpacked**, and select this `extension/`
   directory.
3. Copy the extension's id shown on its card (a 32-character string).
4. Add it to the repo root's `.env`:
   ```
   EXTENSION_ORIGINS=chrome-extension://<the-id-you-copied>
   ```
5. Restart the backend so it picks up the new CORS allow-list entry:
   ```
   docker compose up -d --force-recreate backend
   ```
6. Click the CyberShield icon in the toolbar, or visit any `http(s)://`
   page — it will be scanned automatically (Auto Scan is on by default).

If you change any file under `src/`, click the refresh icon on the
extension's card in `chrome://extensions` to reload it.

## Configuration

Open the extension's options page (right-click the toolbar icon → **Options**,
or click **Settings** in the popup). If your backend/frontend aren't on the
default `localhost` ports, update **CyberShield API URL** and
**CyberShield Dashboard URL** there.

## Tests

```
npm install
npm test
```

Runs the Vitest + jsdom suite (65 tests) against a fake `chrome.*` mock —
see the main README's Phase 6 section for what's covered.
