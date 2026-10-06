# CyberShield — System Walkthrough

> **How this document was produced.** Every claim below was verified by reading the actual source files in this repository (backend Python, frontend TypeScript, the browser extension's JavaScript, Alembic migrations, Docker/nginx configuration, and the test suites) on 2026-08-11. Function names, file paths, route paths, table names, numeric constants (rate limits, score impacts, thresholds, TTLs), and test counts are copied from the real code, not from the README's prose or from memory. Where the README, a docstring, or a code comment claims something I could **not** independently confirm in the code, or where I found the two disagreeing, it is called out explicitly in the relevant section (see especially §9). Nothing here is invented or "rounded up" to sound more finished than the code actually is.

---

## 1. System Overview

**CyberShield** is a web-based phishing-detection platform. A logged-in user can submit three kinds of content for analysis:

- a **URL** (`POST /api/v1/url/scan`),
- raw **email source** — pasted text or an uploaded `.eml` file (`POST /api/v1/email/scan`),
- a **QR code image** (`POST /api/v1/qr/scan`),

and get back a **Trust Score** (0–100), a **Risk Level** (`Safe` / `Low Risk` / `Suspicious` / `Dangerous`), a list of human-readable reasons the score is what it is, and recommendations. Every scan is persisted to the user's own history, surfaced on a personal dashboard, and feeds a platform-wide Threat Intelligence view.

Beyond scanning, the platform includes: user accounts with email verification and optional Google Sign-In; a personal "Block List" a user can add dangerous sites to, enforced automatically by an installable Chrome/Edge browser extension; an admin panel (role-gated) for managing users, the domain blacklist, detection-rule toggles, and audit logs; and a set of account-security features (password reset, account lockout, session management).

**Who it's for**, based on what's actually built: individual end users protecting themselves from phishing links/emails/QR codes (the scanners, dashboard, browser extension, personal block list), and a platform administrator (the `/admin/*` panel, gated to accounts with `role="admin"`). There is no multi-tenant/organization concept anywhere in the schema — every table with a `user_id` column scopes data to one individual account.

The repository itself documents its own development as a sequence of numbered "Phases" (visible in code comments and migration names, e.g. `phase 9 active protection`, `phase 10: account lockout fields`, `phase 11: google sign-in`). This walkthrough does not organize itself by phase — it organizes by what the system *is*, today — but phase numbers are kept in citations where the code itself uses them, since they're a real, verifiable part of the commit/migration history.

---

## 2. Architecture

### 2.1 The four layers

```
┌─────────────────────────────┐        ┌──────────────────────────────┐
│   Browser (user)            │        │   Browser Extension (MV3)     │
│   React SPA — Vite dev      │        │   background.js / content.js  │
│   server (5173) or nginx    │        │   — same cookies as the SPA   │
│   in production             │        │                                │
└──────────────┬───────────────┘        └──────────────┬─────────────────┘
               │  fetch/axios, httpOnly cookies         │  fetch, chrome.cookies
               │  + X-CSRF-TOKEN header                 │  + X-CSRF-TOKEN header
               ▼                                        ▼
        ┌────────────────────────────────────────────────────┐
        │        Flask API — /api/v1/*  (backend:5000)        │
        │  routes/v1/*.py → services/*.py → models (SQLAlchemy)│
        └───────────────────────┬──────────────────────────────┘
                                 │  SQLAlchemy ORM (psycopg2 driver)
                                 ▼
                     ┌───────────────────────┐
                     │   PostgreSQL 16        │
                     │   (postgres container) │
                     └───────────────────────┘
```

This diagram is a description of what `docker-compose.yml` actually wires up: three services — `postgres` (image `postgres:16-alpine`), `backend` (built from `backend/Dockerfile`, Flask dev server on `:5000`), `frontend` (built from `frontend/Dockerfile`, Vite dev server on `:5173`) — plus a fourth artifact, the browser extension, which is **not** a Docker service at all; it's loaded unpacked into a real browser and talks to the same backend over HTTP.

- **Frontend** (`frontend/`): React 18 + TypeScript + Vite + Tailwind CSS + React Router. All API calls go through one axios instance, `frontend/src/lib/api.ts`, configured with `baseURL: import.meta.env.VITE_API_BASE_URL` and `withCredentials: true` (so httpOnly cookies are sent automatically). A response interceptor there catches a `401`, calls `POST /auth/refresh` once, and retries the original request — this is the *only* place token refresh happens on the web side.
- **Backend** (`backend/`): Flask, organized as `routes/v1/*.py` (thin — parse request, call a schema, call a service, return JSON) → `services/*.py` (the actual business logic, one file per concern) → `models/*.py` (SQLAlchemy `db.Model` classes). `backend/app/__init__.py`'s `create_app()` is the single factory that wires config, extensions, blueprints, JWT callbacks, security headers, and request-metrics middleware together.
- **Database**: PostgreSQL 16 in production/dev (via Docker), SQLite in-memory for the test suite (`TestingConfig.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"` in `backend/app/config.py`). JSON-typed columns use `db.JSON().with_variant(JSONB, "postgresql")` so they're plain JSON under SQLite but real indexable `JSONB` under Postgres — this pattern repeats in `models/scan.py`, `models/email_scan.py`, `models/qr_scan.py`, `models/blocked_website.py`, `models/audit_log.py`.
- **Browser extension** (`extension/`): a Manifest V3 extension with **no bundler/build step** — every file under `extension/src/` is exactly what Chrome loads. It has no login screen of its own; it reads the same httpOnly cookies the web app's login already set in that browser profile.

### 2.2 The `/api/v1` REST API

Every backend route is registered under one prefix in `backend/app/routes/v1/__init__.py`:

```python
api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")
api_v1_bp.register_blueprint(auth_bp, url_prefix="/auth")
api_v1_bp.register_blueprint(users_bp, url_prefix="/users")
api_v1_bp.register_blueprint(scans_bp, url_prefix="/url")
api_v1_bp.register_blueprint(email_scans_bp, url_prefix="/email")
api_v1_bp.register_blueprint(qr_scans_bp, url_prefix="/qr")
api_v1_bp.register_blueprint(scan_center_bp, url_prefix="/scans")
api_v1_bp.register_blueprint(reports_bp, url_prefix="/reports")
api_v1_bp.register_blueprint(dashboard_bp, url_prefix="/dashboard")
api_v1_bp.register_blueprint(profile_bp, url_prefix="/profile")
api_v1_bp.register_blueprint(settings_bp, url_prefix="/settings")
api_v1_bp.register_blueprint(notifications_bp, url_prefix="/notifications")
api_v1_bp.register_blueprint(threats_bp, url_prefix="/threats")
api_v1_bp.register_blueprint(extension_bp, url_prefix="/extension")
api_v1_bp.register_blueprint(admin_dashboard_bp, url_prefix="/admin/dashboard")
api_v1_bp.register_blueprint(admin_users_bp, url_prefix="/admin/users")
api_v1_bp.register_blueprint(admin_scans_bp, url_prefix="/admin/scans")
api_v1_bp.register_blueprint(admin_blacklist_bp, url_prefix="/admin/blacklist")
api_v1_bp.register_blueprint(admin_rules_bp, url_prefix="/admin/rules")
api_v1_bp.register_blueprint(admin_audit_bp, url_prefix="/admin/audit-logs")
api_v1_bp.register_blueprint(admin_system_bp, url_prefix="/admin/system")
api_v1_bp.register_blueprint(admin_stats_bp, url_prefix="/admin/stats")
api_v1_bp.register_blueprint(protection_bp, url_prefix="/protection")
```

Plus one route registered directly on the Flask app, **outside** `/api/v1` on purpose: `GET /health` (`backend/app/__init__.py`), used by Docker's `HEALTHCHECK` — deliberately unauthenticated, and it does a real database check via `system_monitoring_service.get_database_status()`, returning `503` if Postgres is unreachable.

**The most important routes**, grouped by what they actually do (verified in each route file):

| Concern | Route | File : function |
|---|---|---|
| Register | `POST /auth/register` | `routes/v1/auth.py : register()` |
| Login | `POST /auth/login` | `routes/v1/auth.py : login()` |
| Refresh access token | `POST /auth/refresh` | `routes/v1/auth.py : refresh()` |
| Logout | `POST /auth/logout` | `routes/v1/auth.py : logout()` |
| Google Sign-In | `GET /auth/google/login`, `GET /auth/google/callback` | `routes/v1/auth.py : google_login(), google_callback()` |
| Email verify / resend | `POST /auth/verify-email`, `POST /auth/resend-verification` | `routes/v1/auth.py` |
| Password reset | `POST /auth/forgot-password`, `POST /auth/reset-password` | `routes/v1/auth.py` |
| Scan a URL | `POST /url/scan` | `routes/v1/scans.py : scan_url_endpoint()` → `services/scan_service.py` → `services/url_scanner/engine.py : scan_url()` |
| Scan an email | `POST /email/scan` | `routes/v1/email_scans.py : scan_email_endpoint()` → `services/email_scanner/engine.py : analyze_email()` |
| Scan a QR image | `POST /qr/scan` | `routes/v1/qr_scans.py : scan_qr_endpoint()` → `services/qr_scanner/engine.py : analyze_qr_content()` |
| Unified scan history (all 3 types) | `GET /scans` | `routes/v1/scan_center.py` → `services/unified_scan_service.py` (one `UNION ALL` SQL query across the three history tables) |
| Structured report | `GET /reports/<scanner_type>/<id>` | `routes/v1/reports.py : get_report()` |
| Personal block list | `GET/POST/DELETE /protection/blocklist` | `routes/v1/protection.py` → `services/block_list_service.py` |
| Extension sync | `GET /protection/sync` | `routes/v1/protection.py : sync_for_extension()` |
| Admin: users | `GET /admin/users`, `PATCH /admin/users/<id>/status` | `routes/v1/admin_users.py` |
| Admin: platform stats | `GET /admin/stats` | `routes/v1/admin_stats.py` |

Auth pattern used everywhere except the two intentionally-open routes (`/health`, `POST /auth/register|login`): a JWT **access token** delivered as an httpOnly cookie, validated by Flask-JWT-Extended's `@jwt_required()` (or the richer `@require_permission(...)` / `@require_not_restricted(...)` wrappers described in §5). Every mutating (`POST`/`PUT`/`PATCH`/`DELETE`) request additionally requires an `X-CSRF-TOKEN` header matching the `csrf_access_token` cookie (double-submit pattern) — enforced by Flask-JWT-Extended's built-in `JWT_COOKIE_CSRF_PROTECT = True` (`backend/app/config.py`), not custom code.

---

## 3. Database

CyberShield uses **Alembic** migrations (`backend/migrations/versions/`, `flask db migrate` / `flask db upgrade`) — there is no hand-edited schema. As of this writing there are **12 migration files**, applied in this real dependency order (verified by reading each file's `revision`/`down_revision` pair, not by filename sort):

1. `9929dee9046c` — **Initial migration**: `users`, `token_blocklist`, `user_tokens`
2. `4510943deac3` — Add `scan_history` and `blacklist_entries`
3. `177cff4e01fb` — Switch `scan_history`'s JSON columns to `JSONB` on Postgres
4. `c1c6ec70cefc` — Add `email_scan_history`
5. `da63d791cb98` — Add `qr_scan_history`
6. `d57f7940d777` — user profile fields, `user_settings`, `notifications`, `user_sessions`, `duration_ms`
7. `12ba92ef9119` — add `session_key` to `user_sessions`
8. `ec2bbce90d8a` — `audit_logs`, `detection_rules`, `blacklist_entries.enabled`, `*.source` columns
9. `396d35d5a290` — **Phase 9**: `blocked_websites`, `user_settings.protection_mode`
10. `a1f3c9d0e5b2` — **Phase 10**: account-lockout fields on `users` (`failed_login_attempts`, `locked_until`)
11. `b7c1e4d9a3f6` — **Phase 11**: Google Sign-In (`users.google_id`, `users.password_hash` made nullable)
12. `c362fb36e69c` — `users.status`, `user_restrictions` table

### 3.1 Tables (14 total), what they store, and their real foreign keys

| Table | Model file | Key columns | Foreign keys |
|---|---|---|---|
| `users` | `models/user.py` | `id` (uuid string, PK), `username`, `email` (both unique), `password_hash` (nullable — see §5.9), `google_id` (nullable, unique), `role` (`user`\|`admin`), `is_verified`, `is_active`, `status` (`active`\|`suspended`\|`removed`), `failed_login_attempts`, `locked_until`, `phone`, `country`, `bio`, `avatar_url` | — |
| `token_blocklist` | `models/token.py` | `jti` (unique), `token_type`, `expires_at` | `user_id → users.id` |
| `user_tokens` | `models/user_token.py` | `token_hash` (SHA-256, unique — **the raw token is never stored**), `purpose` (`email_verification`\|`password_reset`), `expires_at`, `used_at` | `user_id → users.id` |
| `scan_history` | `models/scan.py` | `url`, `trust_score`, `risk_level`, `scan_result` (JSON), `analysis_details` (JSON), `duration_ms` (nullable), `source` (`web`\|`extension`) | `user_id → users.id` |
| `email_scan_history` | `models/email_scan.py` | `sender_display_name`, `sender_email`, `subject`, `trust_score`, `risk_level`, `link_count`, `attachment_count`, `scan_result` (JSON), `analysis_details` (JSON) | `user_id → users.id` |
| `qr_scan_history` | `models/qr_scan.py` | `content_type`, `raw_content`, `trust_score`, `risk_level`, `scan_result` (JSON), `analysis_details` (JSON) | `user_id → users.id` |
| `blacklist_entries` | `models/blacklist.py` | `domain` (unique), `reason`, `enabled` | `added_by_user_id → users.id` (nullable) |
| `detection_rules` | `models/detection_rule.py` | `key` (e.g. `"url.https_check"`, unique), `category` (`url`\|`email`), `label`, `severity`, `enabled`, `version` | — |
| `audit_logs` | `models/audit_log.py` | `action`, `status` (`success`\|`failure`), `ip_address`, `details` (JSON) | `user_id → users.id` (nullable — e.g. a failed login for an email that matches no account) |
| `user_settings` | `models/user_settings.py` | `theme`, `language`, `timezone`, four `notify_*` booleans, `profile_visibility`, `protection_mode` | `user_id → users.id` (this **is** the primary key — a true 1:1) |
| `notifications` | `models/notification.py` | `type`, `title`, `message`, `scanner_type`/`scan_id` (nullable, points back at a scan), `is_read` | `user_id → users.id` |
| `user_sessions` | `models/user_session.py` | `refresh_jti` (unique), `session_key` (unique), `user_agent`, `ip_address`, `last_seen_at`, `revoked_at`, `expires_at` | `user_id → users.id` |
| `blocked_websites` | `models/blocked_website.py` | `domain`, `trust_score`, `risk_level`, `reasons` (JSON), `scanner_type`, `scan_id` (nullable), `is_active`, `blocked_at`, `unblocked_at` — unique on `(user_id, domain)` | `user_id → users.id` |
| `user_restrictions` | `models/user_restriction.py` | `feature` (`url`\|`email`\|`qr`\|`reports`), `restricted_at` — unique on `(user_id, feature)` | `user_id → users.id`, `restricted_by_user_id → users.id` (nullable) |

**Relationship shape**: `users` is the hub — every other table has a `user_id` foreign key back to it (nullable only on `audit_logs.user_id`, since a failed-login-with-unknown-email audit entry has no real user to attach to). There is exactly one declared SQLAlchemy `relationship()` in the codebase: `User.tokens` (`models/user.py`), a one-to-many to `UserToken` with `cascade="all, delete-orphan"`. Every other table is queried directly by `user_id` filter in its service module rather than via an ORM relationship — a deliberate, consistent pattern across the codebase (e.g. `admin_user_service.py`, `unified_scan_service.py`).

The three scan-history tables (`scan_history`, `email_scan_history`, `qr_scan_history`) are **not** merged into one polymorphic table — each keeps its own auto-incrementing `id`, so a `url` scan `#1` and a `qr` scan `#1` can both exist. `services/unified_scan_service.py` presents them as one logical feed via a SQL `UNION ALL`, addressed by a compound `(scanner_type, id)` key rather than a fabricated single ID space (this is what powers `GET /scans`, the "Scan Center").

---

## 4. Detection Engine (URL, Email, QR)

All three scanners share the same shape: a `ScanContext`/`EmailContext` dataclass built once, a list of independent **rule modules** (each with one `evaluate()` function), and an **engine** that runs the rules and combines their `impact` values into a score. Scoring always starts at **100** and every triggered rule *subtracts* — there is no bonus scoring anywhere in the code.

### 4.1 URL Scanner (`backend/app/services/url_scanner/`)

Entry point: `engine.py : scan_url(raw_url) -> ScanReport`. Steps, read directly from the code:

1. `context.py : build_context()` parses the URL, extracts the hostname, detects whether it's a raw IP, and resolves DNS (`network.py : resolve_hostname()`), producing a `ScanContext`.
2. A private/internal-IP target is rejected outright with a `422` (`engine.py : _is_private_target()`, reusing `network.is_public_ip`) — CyberShield refuses to scan `127.0.0.1`, `169.254.169.254`, etc.
3. `engine.py : _run_rules()` runs the fast, CPU-only rules synchronously, then the three network-bound rules (`ssl_certificate`, `domain_age`, `redirect_check`) concurrently via a `ThreadPoolExecutor`, bounded by an **8-second** deadline (`NETWORK_RULES_TIMEOUT_SECONDS`) — a rule that doesn't finish in time is reported as timed-out rather than blocking the scan.
4. `rule_registry_service.filter_enabled_rules("url", RULES, ...)` filters out any rule an admin has disabled via `PUT /admin/rules/<id>` (see §5.6) — a missing/un-seeded `DetectionRule` row is treated as *enabled* by default.
5. `_score_and_risk()`: `score = 100 + sum(impact for each rule result)`, clamped to `[0, 100]`.
6. `RiskLevel.from_score()` (`app/constants.py`) maps the score to a label: **≥90 → Safe, ≥70 → Low Risk, ≥40 → Suspicious, else → Dangerous.**

**The 11 rules and their exact score impact** (every number below is copied from the corresponding `rules/*.py` file, not estimated):

| Rule file | What it checks | Impact |
|---|---|---|
| `url_length.py` | Unusually long/short URL | up to −15 |
| `https_check.py` | Missing HTTPS | −15 (flat) |
| `ssl_certificate.py` | Real TLS handshake (only if HTTPS); invalid/expired/unverifiable cert | invalid or expired: −20, unknown: −5, valid: 0 |
| `ip_address.py` | Host is a raw IP, not a domain | −30 (flat) |
| `suspicious_keywords.py` | Phishing-lure words (login/verify/bank/wallet/paypal/...) | −6 per match, capped at −24 |
| `special_characters.py` | `@` in host (−20), ≥3 `%` (−10), repeated `-`/`_` (−8 each), smuggled second `//` (−10) — additive, multiple can fire at once | up to roughly −56 in a pathological case |
| `subdomains.py` | Deep subdomain chains | ≥4 subdomains: −15, ≥3: −8 |
| `typosquatting.py` | Levenshtein distance ≤2 (and length difference ≤2) from one of 20 hardcoded `KNOWN_BRAND_DOMAINS` (google.com, paypal.com, amazon.com, ...) | −30 (flat) |
| `domain_age.py` | Real RDAP-style lookup via `domain_age_provider.py` | recently registered: −15, moderately aged: −5, established/unknown: 0 |
| `blacklist_check.py` | Exact match against the `blacklist_entries` table (`enabled=True` rows only) | **−100** (forces the score to 0, i.e. `Dangerous`) |
| `redirect_check.py` | Manually-followed redirect chain (see SSRF note below); >3 hops or a cross-domain final destination | −10 for a long chain, −10 more if cross-domain (both can apply) |

**SSRF protection** (`network.py`, the single most security-relevant file in the URL scanner): every real network call resolves the hostname first via `resolve_hostname()`, validates every resolved IP with `is_public_ip()` (rejects private/loopback/link-local/multicast/reserved/unspecified addresses), and then connects **directly to that already-validated IP** — never re-resolving the hostname at connect time. This closes a DNS-rebinding window where a hostname could resolve to something safe during validation and something internal a moment later. TLS SNI and certificate hostname verification still use the real hostname (`server_hostname=hostname` in `_pinned_request()` and `get_certificate_info()`), so pinning the connection doesn't weaken certificate checking. `safe_follow_redirects()` re-validates and re-pins **every hop** of a redirect chain, not just the first request.

A separate entry point, `engine.py : quick_classify(raw_url)`, runs only the CPU-only rules (no DNS-dependent rules, no TLS handshake, no RDAP lookup, no HTTP request) — this is what the email scanner uses to triage links (§4.2) without turning one email scan into dozens of outbound network calls.

### 4.2 Email Scanner (`backend/app/services/email_scanner/`) — how it reuses the URL Scanner

Entry point: `engine.py : analyze_email(ctx: EmailContext) -> EmailReport`. Parsing (`parser.py`) uses Python's stdlib `email` package on in-memory bytes/text — nothing is ever written to disk. Same 100-point subtract-only scoring as the URL scanner, via 10 rule modules (`sender_analysis`, `display_name_impersonation`, `subject_analysis`, `greeting_analysis`, `urgency_detection`, `threat_language`, `link_analysis`, `attachment_analysis`, `html_analysis`, `grammar_heuristics`).

**The actual reuse mechanism**, verified in `rules/link_analysis.py`:

```python
from app.services.url_scanner.engine import quick_classify
...
def classify_links(links: list[str]) -> list[LinkFinding]:
    for url in links[:MAX_LINKS_TO_CLASSIFY]:  # capped at 20 links per email
        score, risk = quick_classify(url)
        findings.append(LinkFinding(url=url, trust_score=score, risk=risk))
```

Every link found in the email body is run through the *exact same* `url_scanner.engine.quick_classify()` function used everywhere else — there is no second, separate URL-risk implementation inside the email scanner. `link_analysis.py`'s own `evaluate()` then just aggregates: if any link classified as `Dangerous`, the email rule triggers at **−35**; if any classified `Suspicious` (and none Dangerous), **−18**.

### 4.3 QR Scanner (`backend/app/services/qr_scanner/`) — decode → classify → route

1. **Decode**: `decoder.py : decode_qr_image(content: bytes) -> str` — Pillow (`Image.verify()` for structural integrity, format restricted to `{PNG, JPEG, WEBP}`) + `pyzbar.pyzbar.decode()` for the actual barcode read. Entirely in-memory; nothing touches disk.
2. **Classify**: `content_type.py : detect_and_parse(raw_content)` pattern-matches the decoded text into one of: `url`, `email` (`mailto:`), `phone` (`tel:`), `sms`/`smsto:`, `wifi` (`WIFI:...`), `crypto` (recognized URI schemes or address regexes for BTC/ETH/LTC/DOGE/TRON/XRP), `plain_text`, or `unknown`.
3. **Route**: `engine.py : analyze_qr_content()` looks up `HANDLERS[content_type]` (`rules/__init__.py`) and calls it. Two of the handlers are pure re-use, not new detection logic:
   - `rules/url_rule.py` calls `url_scanner.engine.scan_url()` — the **full** scan (not `quick_classify`), including the TLS/RDAP/redirect checks, since a QR code is a single one-off scan, not one of dozens of links.
   - `rules/email_rule.py` builds an `EmailContext` and calls `email_scanner.engine.analyze_email()`, treating the `mailto:` target as the "sender" for impersonation purposes.
   - The other handlers (`sms_analysis.py`, `phone_analysis.py`, `wifi_analysis.py`, `crypto_analysis.py`, `plain_text_analysis.py`, `unknown_analysis.py`) are QR-specific, since there's no URL/email equivalent to reuse for a phone number or a WiFi credential.
4. **WiFi password redaction**: `content_type.py : redact_wifi_raw_content()` strips the plaintext password out of a `WIFI:...;P:secret;;` string with a regex substitution *before* the content ever reaches the API response or the `qr_scan_history` row — verified as the actual code path in `engine.py`, not just a documented intention.

---

## 5. Authentication & Security Tools

This section lists every security-relevant mechanism I could find actual code for, with its file and function. Where the README describes something I could not find implemented, that is stated explicitly rather than assumed.

### 5.1 Password hashing
`flask_bcrypt.Bcrypt` (`backend/app/extensions.py : bcrypt = Bcrypt()`). Hashing/verification calls: `bcrypt.generate_password_hash(password)` and `bcrypt.check_password_hash(...)`, both in `services/auth_service.py` (`register_user`, `authenticate_user`, `reset_password`, `change_password`, `deactivate_account`). No custom work-factor is configured anywhere in `config.py`, so Flask-Bcrypt's own default is used — I could not find an explicit override, so I am not stating a specific round count.

### 5.2 Password strength policy
`backend/app/utils/validators.py : validate_password_strength()` — five regex rules enforced together: ≥8 characters, at least one uppercase, one lowercase, one digit, one special (non-alphanumeric) character. Applied via `RegisterSchema`/`ResetPasswordSchema` in `schemas/auth.py`.

### 5.3 JWT session model
`flask_jwt_extended.JWTManager` (`extensions.py : jwt = JWTManager()`). Configuration, verified in `config.py`:
- `JWT_TOKEN_LOCATION = ["cookies"]` — tokens are **never** exposed to JavaScript.
- `JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)`, `JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)` (30 days if `remember_me` is set — `routes/v1/auth.py : login()` computes `remember_max_age = int(timedelta(days=30).total_seconds())`).
- `JWT_ACCESS_COOKIE_PATH = "/api/v1/"`; `JWT_REFRESH_COOKIE_PATH = "/api/v1/auth/refresh"` — the refresh cookie is scoped so it's **only** ever sent to the refresh endpoint, never leaked to every other request.
- `JWT_COOKIE_SECURE` — `True` by default, explicitly forced `False` only under `DevelopmentConfig`/`TestingConfig`.
- `JWT_COOKIE_SAMESITE = "Lax"`.
- `JWT_COOKIE_CSRF_PROTECT = True` — the double-submit CSRF mechanism described in §2.2.
- Both access and refresh tokens carry a shared `sid` claim (`auth_service.py : issue_token_pair()`, `session_key = secrets.token_urlsafe(16)`) — this is what lets `session_service.py` identify "this login" from requests that only ever carry the *access* token (the refresh cookie's restricted path means it's never present outside `/auth/refresh`).

### 5.4 Token revocation (logout / forced session kill)
`models/token.py : TokenBlocklist` — every revoked `jti` is written here. `_register_jwt_callbacks()` in `app/__init__.py` wires `@jwt.token_in_blocklist_loader` to `auth_service.is_token_revoked(jti)`, checked automatically by Flask-JWT-Extended on **every** authenticated request. `auth_service.py : revoke_token()` is the one function that writes to this table; called from `POST /auth/logout`, from `DELETE /settings/account` (self-deactivation), and — as of the admin user-management work — from `admin_user_service.py : set_user_status()` whenever an admin suspends or removes a user (via `session_service.revoke_all_other_sessions(user_id, current_session_key=None)`, which walks every live `UserSession` row for that user and blocklists each one's `refresh_jti`).

**A real, verified limitation, not glossed over**: this revokes *refresh* tokens immediately, which blocks `/auth/refresh` and new logins right away. An already-issued **access token** (≤15 min TTL) is not individually blocklisted by that path, because nothing in the schema persists a lookup from `user_id → currently-live access-token jti`. I confirmed by grepping the whole backend that Flask-JWT-Extended's `current_user` proxy (which *would* need a per-request `is_active`/`status` check to close this gap) is never actually referenced anywhere in `routes/` — `@jwt.user_lookup_loader` is registered in `app/__init__.py` but is dead code in practice, since no route calls `current_user`. This means the worst-case window between an admin suspending a user and every one of that user's live requests actually stopping is bounded by the 15-minute access-token TTL, not zero.

### 5.5 Account lockout (Phase 10)
`auth_service.py` — `MAX_FAILED_LOGIN_ATTEMPTS = 5`, `LOCKOUT_DURATION_MINUTES = 15`. `authenticate_user()` increments `User.failed_login_attempts` on a wrong password and sets `User.locked_until = utcnow() + timedelta(minutes=15)` once the 5th failure is reached; a locked account's login attempt is rejected with a `403` **before** the password is even checked (`if user.locked_until is not None and user.locked_until > utcnow(): raise APIError(...)`) — this is checked first specifically so a locked account never leaks whether the submitted password would otherwise have been correct.

### 5.6 Role-based access control
`backend/app/rbac.py`. Not a bare `if role == "admin"` check — a permission matrix:

```python
PERMISSIONS = {
    Role.ADMIN: {"users.view", "users.manage", "scans.view", "scans.manage",
                 "blacklist.manage", "rules.manage", "audit.view", "system.monitor"},
    Role.SECURITY_ANALYST: {"users.view", "scans.view", "blacklist.manage", "rules.manage", "audit.view"},
    Role.VIEWER: {"users.view", "scans.view", "audit.view"},
    Role.USER: set(),
}
```

`require_permission(permission)` is a self-contained decorator (includes its own `@jwt_required()`) that reads the `role` claim already embedded in the access token and raises a `403` via `has_permission()` if the caller lacks the permission. **Verified but worth being precise about**: `Role.SECURITY_ANALYST` and `Role.VIEWER` exist as constants and have entries in `PERMISSIONS`, but there is no code path anywhere that assigns either role to a real account — `User.role` can only ever be set to `"user"` (registration default) or `"admin"` (direct database write only; there is deliberately no HTTP endpoint that grants the admin role, including no self-promotion path). Two roles are architecturally ready but not actually usable today.

### 5.7 Per-user feature restrictions
`models/user_restriction.py`, `services/user_restriction_service.py`. `require_not_restricted(feature)` — same self-contained-decorator shape as `require_permission` — checks the `user_restrictions` table fresh on every request (not cached in the JWT, since a restriction needs to take effect the moment an admin sets it) and raises `403` if a row exists for `(current_user_id, feature)`. Applied to: `POST /url/scan`, `POST /email/scan`, `POST /qr/scan`, `POST /extension/scan` (gated by the `url` feature — deliberately, since it's the same underlying capability as `/url/scan`), and both `GET /reports/<type>/<id>` and `POST /reports/<type>/<id>/export` (gated by a separate `reports` feature, independent of scanner type). It is **not** applied to the scan-history/list endpoints — a restriction blocks performing a *new* scan of that type, not viewing scans made before the restriction was set.

### 5.8 Rate limiting
`flask_limiter.Limiter` (`extensions.py : limiter = Limiter(key_func=get_remote_address)`), backed by `RATELIMIT_STORAGE_URI` (defaults to `memory://` — per-process, documented in `.env.production.example` as needing a shared store like Redis for a real multi-worker deployment). Every `@limiter.limit(...)` call I found by grepping `backend/app/routes/`, verbatim:

| Route | Limit |
|---|---|
| `POST /auth/register` | 5/min |
| `POST /auth/login` | 10/min |
| `POST /auth/forgot-password` | 5/min |
| `POST /auth/reset-password` | 5/min |
| `POST /auth/resend-verification` | 3/min |
| `GET /auth/google/login` | 10/min |
| `POST /url/scan` | 20/min |
| `POST /email/scan` | 15/min |
| `POST /qr/scan` | 15/min |
| `POST /extension/scan` | 20/min |
| `POST /protection/blocklist`, `DELETE .../<id>`, `POST .../<id>/restore` | 30/min each |
| `POST /protection/report` | 15/min |
| `POST /protection/extension-blocked-event` | 60/min |
| `DELETE /settings/account` | 3/min |
| Every mutating `/admin/*` route (deactivate/reactivate/status/restrictions/blacklist add-remove-enable-disable/rule toggle) | 30/min (15/min for `admin/scans` bulk-delete) |

Additionally: `POST /auth/resend-verification` has a **second, independent** cap beyond the IP-based limiter above — `auth_service.py : resend_verification_email()` counts this account's `email_verification_sent` audit-log entries in the last hour (`VERIFICATION_RESEND_MAX_PER_HOUR`, default 3, `config.py`) and silently skips sending once the cap is hit, **without changing the HTTP response**, specifically so the cap itself can't be used to fingerprint whether an account exists (see §5.11).

### 5.9 Google Sign-In (Phase 11)
`authlib.integrations.flask_client.OAuth` (`extensions.py : oauth = OAuth()`). Only registered as a real provider if both `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set (`app/__init__.py : _init_google_oauth()`) — an unconfigured deployment leaves `/auth/google/*` returning a clean `501`, not a broken app. `routes/v1/auth.py : google_callback()` calls `oauth.google.authorize_access_token()`, which — per Authlib, not custom code — validates the returned `id_token`'s signature against Google's real JWKS, issuer, audience, nonce, and expiry. The route additionally checks `claims.get("email_verified")` itself and refuses to sign in an unverified Google email. `auth_service.py : find_or_create_google_user()` links a Google identity to an existing password account by matching email (safe, since Google has already verified that email) rather than creating a duplicate user; `User.password_hash` is nullable specifically to support a Google-only account that never sets a password (verified in `models/user.py`).

### 5.10 Email verification tokens
`models/user_token.py`, `services/token_service.py`. `issue_token()` generates a token with `secrets.token_urlsafe(32)` (cryptographically secure), stores **only** `hashlib.sha256(raw_token).hexdigest()` in `user_tokens.token_hash`, and deletes any previous *unused* token for the same `(user_id, purpose)` before inserting — the raw token itself is never persisted, only ever emailed. `consume_token()` marks `used_at` on success, so a token cannot be replayed; a call with an already-used or expired token returns `None`, and the route (`verify_email()` in `auth_service.py`) turns that into a generic "invalid or expired" `400`. Default TTL: 24 hours (`EMAIL_VERIFICATION_TOKEN_TTL_HOURS`, `config.py`), 30 minutes for a password-reset token (`PASSWORD_RESET_TOKEN_TTL_MINUTES`).

### 5.11 Account-enumeration resistance
Verified in three places: `auth_service.py : request_password_reset()` returns silently whether or not the email matches a user; `resend_verification_email()` does the same, plus the resend-cap behavior in §5.8; `forgot_password()`'s route always returns the same `200 {"message": "If that email exists, a reset link has been sent."}` regardless.

### 5.12 SSRF protection
Described in full in §4.1 — `services/url_scanner/network.py`. This is a URL-scanning-engine concern more than a generic "auth" concern, but it's a real, code-verified security control, so it's listed here for completeness rather than only in §4.

### 5.13 Security headers
`middleware/security_headers.py : register_security_headers()`, an `@app.after_request` hook, sets on **every** response: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: geolocation=(), microphone=(), camera=()`, `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'` (justified in the code comment: this is a pure JSON API serving no HTML/CSS/JS of its own, so a maximally restrictive CSP costs nothing), `Cross-Origin-Opener-Policy: same-origin`, `Cross-Origin-Resource-Policy: cross-origin` (deliberately not `same-origin` — the frontend and the browser extension are legitimate cross-origin consumers of this API), and, only when `not app.debug`, `Strict-Transport-Security: max-age=31536000; includeSubDomains`. The **frontend's** static assets get an equivalent set of headers from `frontend/nginx.conf` in production (a different, appropriately-scoped CSP suited to serving HTML/JS, not JSON).

### 5.14 CORS
`flask_cors.CORS` (`extensions.py`), initialized in `app/__init__.py : _init_extensions()` with `resources={r"/api/*": {"origins": [FRONTEND_ORIGIN, *EXTENSION_ORIGINS]}}, supports_credentials=True`. `EXTENSION_ORIGINS` is an explicit, operator-populated allow-list of `chrome-extension://<id>` origins (`config.py : _list_env()`) — not a wildcard, specifically so an arbitrary other installed extension can't ride a user's CyberShield session cookie.

### 5.15 Mass-assignment prevention
Every update-style endpoint I checked (`PUT /users/me`, `PUT /profile`, `PUT /settings`) uses a marshmallow schema with an explicit field allow-list (e.g. `UPDATABLE_PROFILE_FIELDS`) rather than blindly applying a request body to the model — verified by reading `schemas/auth.py`, `schemas/settings.py`, and the corresponding service functions in `services/`.

### 5.16 Audit logging
`models/audit_log.py`, `services/audit_service.py : log_action(user_id, action, ip_address, status, **details)`. Called from route handlers after login/logout, profile/settings updates, report generation, scan deletion, extension scan events, password reset request/completion, password change, blacklist add/remove, rule toggle, and every admin user-management action (deactivate/reactivate/status-change/restriction add-remove) — one extra call appended after each existing success path, not a rewrite of the underlying logic. `GET /admin/audit-logs` (permission `audit.view`) exposes this, filterable by `action`, `user_id`, `status`, `search` (matches `ip_address`), and `date_from`/`date_to`.

### 5.17 File upload validation (email `.eml` / QR image)
Enforced in-memory, never touching disk, verified in `routes/v1/email_scans.py` and `services/qr_scanner/decoder.py`: a hard WSGI-level `MAX_CONTENT_LENGTH` (`config.py`, 8 MB default) rejects oversized requests before buffering; the email route additionally enforces its own tighter limits (200 KB pasted text, 5 MB file, checked in `schemas/email_scan.py : validate_email_upload()`); uploaded filenames are extension-checked (`.eml`/`.msg` — `.msg` always returns a clean `422`, see §9); QR uploads are format-restricted to `{PNG, JPEG, WEBP}` and validated with `Image.verify()` before decoding, with Pillow's own `MAX_IMAGE_PIXELS` guard protecting against a decompression-bomb-style oversized image.

---

## 6. Browser Extension

`extension/` is Manifest V3, **plain JavaScript/HTML/CSS with no bundler** — confirmed by `manifest.json` referencing `.js` files directly and there being no build config beyond `vitest.config.js` (which is test-only tooling, not a production bundler).

**How it authenticates**: it doesn't, on its own. `extension/src/shared/api-client.js`'s docstring and code both confirm it reuses the same httpOnly `access_token`/`refresh_token` cookies the web app sets when the user logs in via the CyberShield website *in that same browser*. Because a Manifest V3 service worker has no `document.cookie`, CSRF tokens are read via the `chrome.cookies` API (`api-client.js : getCookie()`) instead. Its 401 → `POST /auth/refresh` → retry-once logic in `request()` is a line-for-line match of the web frontend's axios interceptor.

**How it decides what to scan**: `background.js` listens to `chrome.webNavigation.onCommitted` and `onHistoryStateUpdated` (the latter specifically to catch SPA `pushState` navigations that `tabs.onUpdated` alone would miss). For each scannable top-frame navigation (`frameId === 0`, URL doesn't match `SKIPPED_URL_PATTERN`), it calls `getOrScanVerdict()`, which: checks a local 5-minute result cache (`storage.js`) → checks for an in-flight de-duped request for the same URL → applies a client-side sliding-window rate limiter (`canMakeRequest()`, `RATE_LIMIT_MAX_REQUESTS`/`RATE_LIMIT_WINDOW_MS` from `constants.js`) → calls `CyberShield.api.scanUrl(url, settings)`.

**Which endpoint it actually calls**, verified in `api-client.js : scanUrl()`:
```js
const path = settings.privacyMode ? "/extension/scan" : "/url/scan";
```
By default it calls the **exact same** `POST /url/scan` the web dashboard's URL Scanner page calls — an automatically-scanned page shows up in the user's real Scan Center history exactly like a manual scan would. Only when the user has turned on "Privacy Mode" (an options-page toggle) does it call `POST /extension/scan` instead — the one backend route added specifically for the extension, which calls the identical `url_scanner.engine.scan_url()` function but skips the `ScanHistory` database write entirely (verified in `routes/v1/extension.py`).

**Active Protection / hard blocking (Phase 9)**: separately from the per-visit scan, `background.js` periodically polls `GET /protection/sync` (`syncProtection()`, on an alarm — `PROTECTION_SYNC_INTERVAL_MINUTES`) and caches the user's Personal Block List locally. `findHardBlock()` checks this cache **before** any scan happens — a domain on the block list never even reaches the scan path. Depending on the user's `protection_mode` setting (`warn_only` / `ask_before_blocking` / `auto_block_dangerous` / `auto_block_dangerous_suspicious`), a fresh Dangerous/Suspicious result can also trigger `maybeAutoBlock()`, which calls `POST /protection/blocklist` itself — the same endpoint the dashboard's "Block Website" button uses.

**How the warning page is displayed**: `content.js` asks the background worker for a verdict (`GET_OR_SCAN_VERDICT` message) and, only if the result is blocking, builds an overlay via `buildOverlay()` (soft warning, has a "Continue Anyway" button) or `buildBlockedOverlay()` (hard block from the Personal Block List — **deliberately has no "Continue Anyway" button**, per the code comment: "a block the user explicitly chose to enforce shouldn't be one click away from bypassing itself"). Both are rendered inside `overlayHost.attachShadow({ mode: "closed" })` — a **closed** shadow root, which the host page's own JavaScript cannot reach via `element.shadowRoot` to inspect, restyle, or remove. The warning content (site, trust score, reasons, recommendations) is inserted via `innerHTML` after every dynamic value is passed through a local `escapeHtml()` helper (a `textContent`-based sanitizer), not raw string interpolation.

---

## 7. Testing

Numbers below were obtained by actually **running** the test suites in the running Docker containers, not by reading a claimed count.

### 7.1 Backend
`cd backend && pytest`. Verified via `pytest --collect-only -q`: **473 tests collected**, and a full run reports **473 passed, 0 failed**. These are almost entirely integration-style tests hitting real Flask routes through `app.test_client()` against an in-memory SQLite database (`tests/conftest.py : client` fixture) — plus a smaller set of direct unit tests against individual rule modules (e.g. `test_url_rules.py`, `test_email_rules.py`) and pure-function tests (e.g. `test_url_network.py` for the SSRF helpers). Outbound network calls the URL scanner would normally make (SSL check, redirect-follow, WHOIS/RDAP domain-age lookup) are stubbed in `conftest.py`'s autouse `stub_url_scanner_network_calls` fixture, so the whole suite runs fully offline and deterministically. The largest individual files are `test_email_rules.py` (30 tests) and `test_url_rules.py` (25 tests); every route module (auth, admin sub-resources, scans, reports, protection, settings, notifications, threat intel) has its own dedicated `test_*_routes.py` file.

### 7.2 Browser extension
`cd extension && npm test` (Vitest + jsdom, config in `vitest.config.js`). Verified by actually running `npx vitest run`: **10 test files, 89 tests, all passing** (`api-client.test.js` 12, `protection.test.js` 11, `storage.test.js` 10, `content.test.js` 9, `options.test.js` 6, `popup.test.js` 11, `background.test.js` 14, `constants.test.js` 6, `regression.test.js` 6, `performance.test.js` 4). These mock `chrome.*` APIs (there's a `tests/helpers/` fixture for this) and drive the real extension code — e.g. the background-worker tests dispatch through the actual `chrome.runtime.onMessage` listener, and the content-script tests intercept `Element.attachShadow` to assert a *closed* shadow root is really used, rather than weakening that security property just to make it testable.

> **Discrepancy found**: the README's Phase 6 section states "65 tests." Running the suite today shows **89 passing tests across 10 files** — more than the README claims, not fewer, but the number in the README is stale/incorrect as of this reading. I'm stating the number I actually measured.

### 7.3 What kind of tests these are
Both suites are dominated by **integration tests** (real routes / real message-passing, in-memory or mocked infrastructure) rather than isolated unit tests, with a meaningful minority of true unit tests for pure functions (Levenshtein distance, WiFi-string parsing, redirect validation, etc.). There is no browser end-to-end test framework (no Playwright/Cypress/Selenium config anywhere in the repo) — the closest to that is the extension having been "load-tested unpacked in real Chromium" per the README's own account, which is a manual verification step, not an automated test I can independently re-run or count.

---

## 8. Infrastructure / Deployment

### 8.1 Docker Compose (development) — `docker-compose.yml`
Three services: `postgres` (`postgres:16-alpine`, healthcheck via `pg_isready`), `backend` (built from `backend/Dockerfile`, bind-mounts `./backend:/app` for live-reload, runs `flask run --debug`), `frontend` (built from `frontend/Dockerfile`, bind-mounts `./frontend:/app` with a separate named volume for `node_modules`, runs the Vite dev server). `backend` depends on `postgres` being healthy before starting.

### 8.2 Docker Compose (production) — `docker-compose.prod.yml`
Same three services, different images: `Dockerfile.prod` for both backend and frontend, `FLASK_ENV=production`, no bind-mounted source, Postgres has **no published port** (only reachable from `backend` on the internal compose network). The file's own header comment states it "is NOT wired up to actually deploy anywhere — it's a reviewed, ready-to-use starting point," which matches what's actually in the repo: there's no CI/CD pipeline, no cloud provider config, and no evidence anywhere of this having been pointed at a real server.

- **Backend production image** (`backend/Dockerfile.prod`): `python:3.12-slim`, installs `libpq-dev`, `gcc`, `libzbar0` (the QR decoder's native dependency), runs as a non-root `cybershield` user, has a container `HEALTHCHECK` hitting `GET /health`, and serves via **gunicorn**: `gunicorn --bind=0.0.0.0:5000 --workers=4 --timeout=30 --access-logfile=- --error-logfile=- wsgi:app`.
- **Frontend production image** (`frontend/Dockerfile.prod`): multi-stage — `node:20-alpine` builds the Vite bundle (`VITE_API_BASE_URL` passed as a build `ARG`, since Vite inlines `VITE_*` env vars at build time, not runtime), then `nginx:1.27-alpine` serves the static output using `frontend/nginx.conf` (SPA fallback via `try_files $uri $uri/ /index.html`, gzip, long-cache headers on hashed `/assets/`, its own security headers/CSP as described in §5.13).

### 8.3 Key environment variables
From `.env.example` / `.env.production.example` / `config.py`, grouped by purpose:

- **Secrets**: `SECRET_KEY`, `JWT_SECRET_KEY` (Flask refuses to start without these unless `TESTING`), `POSTGRES_PASSWORD`.
- **Database**: `DATABASE_URL` (assembled from the Postgres vars in compose), `POSTGRES_USER`/`_PASSWORD`/`_DB`/`_PORT`.
- **Cross-origin**: `FRONTEND_ORIGIN`, `FRONTEND_BASE_URL` (also used to build verification/reset links), `EXTENSION_ORIGINS` (comma-separated `chrome-extension://` allow-list), `VITE_API_BASE_URL`.
- **Cookies/proxy**: `JWT_COOKIE_SECURE`, `TRUST_PROXY_HEADERS` (enables `ProxyFix` — off by default; enabling it without a real reverse proxy in front would let a client spoof its own rate-limit identity).
- **Google Sign-In**: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` — both empty by default, which leaves those routes cleanly disabled rather than broken.
- **Email delivery**: `MAIL_BACKEND` (`console` — logs to stdout, the default; or `smtp` — real delivery via `SMTPEmailService`), `MAIL_SERVER`/`MAIL_PORT`/`MAIL_USERNAME`/`MAIL_PASSWORD`/`MAIL_USE_TLS`/`MAIL_FROM`, `VERIFICATION_RESEND_MAX_PER_HOUR`, `EMAIL_VERIFICATION_TOKEN_TTL_HOURS`, `PASSWORD_RESET_TOKEN_TTL_MINUTES`.
- **Rate limiting**: `RATELIMIT_STORAGE_URI` (`memory://` by default — documented as needing a shared store like Redis for multi-worker production correctness).
- **Misc**: `MAX_CONTENT_LENGTH_BYTES` (8 MB default WSGI body-size cap).

---

## 9. What's Still Roadmap (not yet built) — and other discrepancies found

Everything in this section is either a `501`-returning placeholder in real route code, an explicit "not implemented" statement I found in a comment/docstring, or a mismatch between what the README/a comment claims and what I could verify.

### 9.1 Confirmed unimplemented / placeholder endpoints (return `501` in real code)
- `POST /admin/users/<id>/reset-password` — `routes/v1/admin_users.py : reset_password_placeholder()` always raises a `501`.
- `GET /admin/scans/export` — always `501` (`routes/v1/admin_scans.py`).
- `POST /reports/<type>/<id>/export` — `report_export_service.py`'s exporter always raises; PDF export is a prepared interface, not implemented.
- `GET /settings/export` — always `501` (`routes/v1/settings.py`).
- `GET /threats/export` — always `501` (`routes/v1/threats.py`).

### 9.2 Confirmed architecturally-prepared-but-not-usable
- **Security Analyst / Viewer roles** (§5.6): defined in `rbac.py`'s `PERMISSIONS` matrix, but no code path anywhere grants either role to a real account.
- **`.msg` (legacy Outlook) email parsing**: `services/email_scanner/msg_parser.py` always raises a `422` — only `.eml` is actually parsed.
- **Live external threat feed**: `threat_intel_service.py`'s `ThreatFeedProvider` is an abstract interface with exactly one implementation, `InternalThreatFeedProvider`, backed by CyberShield's own blacklist/scan data — no PhishTank/OpenPhish/etc. integration exists.
- **Real caching**: `app/utils/cache.py`'s `@cacheable(ttl_seconds=...)` decorator, applied to a few expensive aggregation functions (e.g. `admin_dashboard_service.get_system_overview`), is a documented **no-op** — every "cached" call is actually recomputed fresh every time.
- **Real request-metrics persistence**: `middleware/request_metrics.py`'s samples live in a bounded in-memory `deque(maxlen=2000)` — resets on every process restart, not a real metrics store.
- **Custom/user-authored detection rules**: `DetectionRule` rows only track metadata (enable/disable, severity, version) for the fixed set of built-in rule modules — there's no mechanism to author a new rule via the admin panel.
- **Memory usage monitoring**: `system_monitoring_service.py` returns `{"available": false, ...}` for memory — no `psutil`-style dependency is present.

### 9.3 Explicitly stated as not implemented (found in README, matches the absence of any corresponding code)
- **Two-factor authentication (TOTP)** — no 2FA field, enrollment flow, or login step exists anywhere in `auth_service.py`/`models/user.py`.
- **Automated database backups** — no backup script/cron/mechanism anywhere in the repo (correctly described as an infrastructure decision outside the codebase).
- **A WAF/CDN in front of production** — not applicable to a code review; no such config exists.
- **Full light-mode re-skin**: the theme *setting* is real and persisted (`user_settings.theme`), but the dashboard sidebar/topbar/canvas stay dark even in "light" mode by design (`frontend/src/lib/theme.ts`) — only the shared UI primitives re-theme.
- **Firefox support**: the extension's `browser-api.js` shim prefers a `browser` global over `chrome`, but the README itself states it has only been tested against Chrome/Edge.
- **Chrome Web Store / Edge Add-ons publishing**: the extension only runs as an unpacked/developer-mode install — no packaging/store-listing artifacts exist.

### 9.4 Discrepancies I found between claims (README/comments) and actual code
- **The top-level Phase list in `README.md` (the numbered "Phase 1–8" summary near the top of the file) does not mention Phase 9 (Active Protection / Personal Block List), Phase 10 (Security Hardening), or Phase 11 (Google Sign-In) at all**, even though all three are fully implemented and verifiable in code: `routes/v1/protection.py` + `models/blocked_website.py` (Phase 9), the account-lockout fields in `models/user.py` + migration `a1f3c9d0e5b2` (Phase 10, though the README does describe this one later, under a "Roadmap" sub-heading rather than its own Phase section), and the Google OAuth routes in `routes/v1/auth.py` + migration `b7c1e4d9a3f6` (Phase 11). In other words: **the code is ahead of the README's own table of contents** — the opposite direction of "claims a feature that doesn't exist," but still a real mismatch worth knowing about.
- **`services/url_scanner/rules/blacklist_check.py`'s docstring is stale**: it says "an admin UI for managing it is planned for a later phase," but a full admin blacklist UI (`AdminBlacklistPage.tsx`, `GET/POST/DELETE /admin/blacklist`, `PUT .../enable`|`disable`) already exists and is tested (`test_admin_blacklist_routes.py`).
- **Extension test count**: the README's Phase 6 section says "65 tests"; running the suite today shows 89 (see §7.2). Not a claim of a missing feature, but a stale number.
- **Extension "Report a false positive/negative"**: the README states the popup's "View Report" link reuses the existing report view rather than adding a second feedback mechanism — verified true; `content.js`/`popup.js` have no separate false-positive-report UI or endpoint.

### 9.5 What I looked for and found **no evidence of at all** (not mentioned anywhere, not partially built)
- Any multi-tenant/organization/team concept.
- Any payment/billing code.
- Any mobile app (iOS/Android) — only the web SPA and the Chrome/Edge extension exist.
- Any machine-learning model or training pipeline — every detection rule in §4 is a deterministic, hand-written heuristic (regex, Levenshtein distance, RDAP lookups, a fixed brand list) — there is no ML anywhere in `url_scanner/`, `email_scanner/`, or `qr_scanner/`.
