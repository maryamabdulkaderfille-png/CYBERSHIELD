# CyberShield

Intelligent Phishing Detection Platform. This repository currently contains:

- **Phase 1: Foundation & Authentication** — the project scaffold, database, and auth system that every later module builds on.
- **Phase 2: URL Phishing Detection Engine** — a modular, rule-based URL scanner with a trust score, risk level, explanations, and scan history.
- **Phase 3: Email Phishing Analyzer** — parses pasted/uploaded email source and scores it against sender, content, link, and attachment heuristics, reusing the Phase 2 URL rules for every link it finds.
- **Phase 4: QR Security Scanner + Reports + Scan Center** — decodes QR codes (upload/drag-drop/paste/camera capture), classifies and scores their content by dispatching to the URL/email engines wherever applicable, generates a structured report for any scan, and unifies all three scanners' history behind one Scan Center view without touching their existing tables.
- **Phase 5: Dashboard Intelligence + Threat Intelligence + Profile + Settings + Notifications** — advanced per-user dashboard widgets (security score, trends, heat map, most-common domains/keywords/scanner), a platform-wide Threat Intelligence Center, an extended user profile with real stats, a fully functional Settings page (theme/language/timezone/notifications/sessions/account deactivation), and a Notification Center — all built from existing scan data, with no new detection logic and no fake data.
- **Phase 6: Browser Extension** — a Manifest V3 Chrome/Edge extension (Firefox-ready architecture) providing real-time phishing protection while browsing: automatic page scanning, a full-page warning for dangerous sites, a popup showing the current site's trust score/risk/reasons, an options page, and browser notifications — reusing the exact same URL Security Engine and auth cookies as the web app, with only one new, minimal, non-persisting API endpoint for its optional Privacy Mode.
- **Phase 7: Enterprise Security + Administration Platform** — a full admin dashboard (System Overview, Users, Scans, Blacklist, Rule Management, Audit Logs, System Monitoring) gated by a new RBAC layer; platform-wide audit logging of security-relevant events; per-rule enable/disable without touching the detection engines; admin-wide generalizations of the existing per-user scan/stats services (`user_id=None`); scan source attribution (web vs. extension); additional security headers (COOP/CORP); and an in-memory request-metrics middleware powering System Monitoring — all additive on top of Phases 1–6, with no detection logic rewritten and no previous API changed.
- **Phase 8 (v1.0): Production Polish + Deployment Preparation** — a full premium landing page (hero, animated stats, product overview, feature/scanner/extension/threat-intel showcases, dashboard preview, demo-labeled testimonials, FAQ, contact, and a real footer with Privacy Policy/Terms pages); a genuine mobile-layout bug fix (a flexbox `min-width` issue that let wide admin tables force the whole page to scroll horizontally); route-based code-splitting for every dashboard/admin page; site-wide keyboard-focus rings and pagination `aria-label`s; a DB-aware `/health` endpoint; rate limiting on every mutating admin route; and a full production deployment path (`Dockerfile.prod` × 2, `docker-compose.prod.yml`, `.env.production.example`) — reviewed and build-tested, not deployed.

## Stack

- **Frontend:** React 18 + Vite + TypeScript + Tailwind CSS + React Router + Framer Motion + Lucide icons
- **Backend:** Python Flask + SQLAlchemy + Flask-Migrate (Alembic) + Flask-JWT-Extended
- **Browser Extension:** Manifest V3, plain JS/HTML/CSS (no bundler), Vitest + jsdom for tests
- **Database:** PostgreSQL 16
- **Infra:** Docker Compose (Postgres + Flask + Vite dev server)

## Prerequisites

- Docker Desktop (with Docker Compose v2)

No local Node.js or Python installation is required — the frontend and backend both run inside containers.

## Setup

1. Copy the environment template and fill in real secrets:

   ```bash
   cp .env.example .env
   ```

   Generate strong values for `SECRET_KEY` and `JWT_SECRET_KEY`:

   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

   Set a strong `POSTGRES_PASSWORD` and update `DATABASE_URL` to match.

2. Build and start everything:

   ```bash
   docker compose up -d --build
   ```

   This starts three services:
   - `postgres` — PostgreSQL 16, exposed on `POSTGRES_PORT` (default `5432`; if that port is already taken on your machine, set it to something else like `5433` in `.env`)
   - `backend` — Flask API on `http://localhost:5000`
   - `frontend` — Vite dev server on `http://localhost:5173`

3. Run database migrations (first time only, or whenever models change):

   ```bash
   docker compose run --rm backend flask --app wsgi.py db upgrade
   ```

4. Open the app: **http://localhost:5173**

## Everyday commands

| Task | Command |
|---|---|
| Start everything | `docker compose up -d` |
| Stop everything | `docker compose down` |
| Tail backend logs | `docker compose logs -f backend` |
| Tail frontend logs | `docker compose logs -f frontend` |
| Run backend tests | `docker compose run --rm backend pytest` |
| Create a new migration after changing models | `docker compose run --rm backend flask --app wsgi.py db migrate -m "message"` |
| Apply migrations | `docker compose run --rm backend flask --app wsgi.py db upgrade` |
| Open a Postgres shell | `docker compose exec postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB>` |

## Project structure

```
CyberShield/
├── docker-compose.yml          # development stack (dev servers, bind-mounted source)
├── docker-compose.prod.yml     # production stack (gunicorn + nginx, no dev servers) — Phase 8
├── .env.example
├── .env.production.example     # production env template — Phase 8
├── backend/
│   ├── Dockerfile               # development image (Flask dev server, --debug)
│   ├── Dockerfile.prod          # production image (gunicorn, non-root user, healthcheck) — Phase 8
│   ├── app/
│   │   ├── config.py           # env-driven config classes (dev/testing/prod)
│   │   ├── extensions.py       # db, migrate, bcrypt, jwt, cors, limiter
│   │   ├── rbac.py              # Role, PERMISSIONS matrix, has_permission(), require_permission() (Phase 7)
│   │   ├── models/              # User, TokenBlocklist, UserToken, ScanHistory, BlacklistEntry, EmailScanHistory,
│   │   │                        #   QRScanHistory, UserSettings, Notification, UserSession,
│   │   │                        #   AuditLog, DetectionRule (Phase 7)
│   │   ├── schemas/             # marshmallow request validation (incl. schemas/admin.py, Phase 7)
│   │   ├── services/
│   │   │   ├── auth_service.py, token_service.py, email_service.py (auth emails)
│   │   │   ├── scan_service.py, email_scan_service.py, qr_scan_service.py  # persistence + stats
│   │   │   ├── unified_scan_service.py  # Scan Center abstraction layer — now also admin-wide (see below)
│   │   │   ├── report_service.py, report_export_service.py  # structured reports + export interface
│   │   │   ├── notification_service.py  # in-app notifications, auto-created from scan results
│   │   │   ├── user_settings_service.py, session_service.py  # Settings page (Phase 5)
│   │   │   ├── user_profile_service.py  # extended profile fields + stats (Phase 5)
│   │   │   ├── dashboard_service.py  # per-user advanced dashboard widgets (Phase 5)
│   │   │   ├── threat_intel_service.py  # platform-wide Threat Intelligence Center (Phase 5)
│   │   │   ├── scan_analytics.py  # keyword/domain/brand aggregation shared by dashboard + threat intel
│   │   │   ├── audit_service.py  # log_action() + list_audit_logs() (Phase 7)
│   │   │   ├── rule_registry_service.py  # filter_enabled_rules() gate in front of both detection engines (Phase 7)
│   │   │   ├── admin_user_service.py, admin_blacklist_service.py, admin_rule_service.py  # admin CRUD (Phase 7)
│   │   │   ├── admin_dashboard_service.py  # System Overview aggregation (Phase 7)
│   │   │   ├── system_monitoring_service.py  # request metrics, DB status, memory placeholder, uptime (Phase 7)
│   │   │   ├── url_scanner/     # URL detection engine (see below)
│   │   │   ├── email_scanner/   # email detection engine (see below)
│   │   │   └── qr_scanner/      # QR detection engine (see below)
│   │   ├── routes/v1/           # auth, users, scans (url), email_scans, qr_scans, scan_center, reports,
│   │   │                        #   dashboard, profile, settings, notifications, threats blueprints,
│   │   │                        #   admin_dashboard, admin_users, admin_scans, admin_blacklist,
│   │   │                        #   admin_rules, admin_audit, admin_system (Phase 7)
│   │   ├── middleware/          # security_headers.py, request_metrics.py (Phase 7)
│   │   └── utils/               # errors, validators, time helpers, timing.py (Stopwatch), cache.py (placeholder),
│   │                            #   client.py (detect_source(), Phase 7)
│   ├── migrations/              # Alembic migrations
│   ├── tests/                   # pytest suite
│   └── wsgi.py
└── frontend/
    ├── Dockerfile                # development image (Vite dev server)
    ├── Dockerfile.prod           # production image (multi-stage: vite build -> nginx) — Phase 8
    ├── nginx.conf                 # SPA fallback routing + gzip + asset caching — Phase 8
    └── src/
        ├── components/
        │   ├── layouts/, forms/, common/   # shared UI, route guards (incl. AdminRoute, AdminLayout, AdminSidebar — Phase 7)
        │   ├── landing/                     # HeroSection, StatsSection, OverviewSection, FeaturesSection,
        │   │                                 #   HowItWorksSection, ScannerShowcaseSection, ExtensionShowcaseSection,
        │   │                                 #   ThreatIntelSection, DashboardPreviewSection, TestimonialsSection,
        │   │                                 #   FaqSection, ContactSection, CtaSection, AnimatedCounter — Phase 8
        │   ├── scanner/                     # TrustScoreGauge, ScanResultCard, RecentScansList
        │   ├── emailScanner/                 # EmailScanResultCard, RecentEmailScansList
        │   ├── qrScanner/                     # QrScanResultCard, QrContentDisplay, RecentQrScansList
        │   ├── scanCenter/                    # UnifiedScanList (shared by Dashboard + Scan Center + Admin Scans)
        │   ├── notifications/                 # NotificationBell (topbar dropdown)
        │   └── dashboard/                      # StatCard, RankedBarList, DailyBarChart, ThreatHeatmap,
        │                                       #   AdvancedIntelligenceSection (Phase 5 hand-rolled charts)
        ├── context/              # AuthContext, ToastContext, NotificationContext (unread-count polling)
        ├── pages/                # public pages + pages/dashboard/* (UrlScannerPage, EmailScannerPage, QrScannerPage,
        │                         #   HistoryPage — unchanged from Phase 3 — ScanCenterPage, ReportPage,
        │                         #   NotificationsPage, ThreatIntelligencePage — Phase 5)
        │                         #   + pages/admin/* (AdminOverviewPage, AdminUsersPage, AdminUserDetailPage,
        │                         #   AdminScansPage, AdminBlacklistPage, AdminRulesPage, AdminAuditLogsPage,
        │                         #   AdminSystemHealthPage — Phase 7; AdminThreatIntelPage — added later,
        │                         #   admin-gated view over /admin/stats)
        │                         #   + PrivacyPolicyPage, TermsOfServicePage — Phase 8
        ├── services/             # authService, scanService, emailScanService, qrScanService, scanCenterService,
        │                         #   reportService, profileService, settingsService, notificationService,
        │                         #   dashboardIntelService, threatIntelService, adminService (Phase 7)
        ├── lib/                  # axios client, cookie/error/risk helpers, theme.ts (Phase 5 theme application),
        │                         #   notifications.ts (icon/color mapping)
        └── types/                # ...types/admin.ts (Phase 7)
```

### `app/services/url_scanner/` — the detection engine

```
url_scanner/
├── types.py               # RuleResult, ScanContext, ScanReport, RiskLevel
├── context.py              # parses the URL + resolves DNS once, shared by every rule
├── network.py              # SSRF-safe outbound requests (DNS/IP allowlisting, safe redirect following, TLS handshake)
├── domain_age_provider.py  # swappable WHOIS/RDAP lookup interface
├── domain_utils.py
├── engine.py               # runs all rules, aggregates the trust score, builds reasons/recommendations
└── rules/                  # one file per detection rule (see API reference below)
```

Each rule is a pure function `evaluate(ctx: ScanContext) -> RuleResult` — adding a new rule means adding one file and registering it in `rules/__init__.py`. `engine.py` never special-cases individual rules.

`quick_classify(url)` is a second entry point alongside `scan_url(url)`: it runs only the CPU-only rules (no TLS handshake, RDAP lookup, or HTTP request), used by the email scanner to triage every link in an email without turning one email scan into dozens of outbound network calls.

### `app/services/email_scanner/` — the email detection engine

```
email_scanner/
├── types.py            # RuleResult, EmailContext, EmailReport, LinkFinding, AttachmentFinding
├── parser.py            # RFC822/.eml parsing via the stdlib `email` package — no disk I/O, ever
├── msg_parser.py         # placeholder for legacy .msg support (see below)
├── brands.py             # known-brand / free-email-domain registry
├── engine.py             # runs all rules, aggregates the trust score, builds reasons/recommendations
└── rules/                # one file per detection rule (see below)
```

Same design as the URL scanner: independent, documented rule modules, no rule knows about any other. `link_analysis.py` reuses `url_scanner.engine.quick_classify` — no URL-parsing logic is duplicated between the two scanners.

### `app/services/qr_scanner/` — the QR detection engine

```
qr_scanner/
├── types.py            # RuleResult, ContentType, QRContext, QRReport
├── decoder.py            # Pillow + pyzbar image decoding — no disk I/O, ever
├── content_type.py        # classifies decoded text into url/email/phone/sms/wifi/crypto/plain_text/unknown
├── engine.py               # dispatches to the right handler and builds the QRReport
└── rules/                  # one handler per content type
    ├── url_rule.py          # hands off to url_scanner.engine.scan_url — full reuse, zero duplication
    ├── email_rule.py        # builds an EmailContext and calls email_scanner.engine.analyze_email
    ├── sms_analysis.py       # reuses email_scanner's urgency_detection/threat_language on the SMS body
    ├── phone_analysis.py, wifi_analysis.py, crypto_analysis.py, plain_text_analysis.py, unknown_analysis.py
```

Unlike the URL/email scanners (where every rule runs on every scan and contributes to one score), QR content types are mutually exclusive — a code is exactly one type at a time — so `engine.py` dispatches to exactly one handler rather than running a uniform rule list. This is a deliberate, documented difference from the other two scanners' architecture, not an inconsistency.

**Reuse in practice:** a URL QR code is scored by the real `scan_url()` (SSL check, RDAP lookup, redirect-follow — the works); a `mailto:` QR code is scored by the real `analyze_email()`, treating the target address as the "sender" for impersonation purposes (a QR that makes you email `support@paypal-verify.com` is the same brand-impersonation pattern the email scanner already catches). Neither path duplicates a single line of detection logic.

**WiFi password handling:** the raw decoded string for a WIFI QR code (`WIFI:S:...;P:secret;;`) contains the plaintext password. `content_type.redact_wifi_raw_content()` strips it before the value is used anywhere — the API response, the persisted history row, and the frontend's "show raw content" toggle all only ever see `P:[REDACTED]`.

## Authentication design

- **Tokens:** JWT access (15 min) + refresh (7 days, 30 days with "remember me"), delivered as `httpOnly` cookies — never exposed to JS.
- **CSRF:** double-submit cookie pattern (`csrf_access_token` / `csrf_refresh_token`), required as an `X-CSRF-TOKEN` header on state-changing requests. The frontend's axios client reads the cookie and attaches the header automatically.
- **Passwords:** bcrypt-hashed; must be 8+ characters with upper, lower, digit, and special character.
- **Logout:** revokes both the access and refresh token's `jti` via a `token_blocklist` table (not just clearing cookies).
- **Email verification / password reset:** one-time tokens are stored only as a SHA-256 hash (`user_tokens` table); the raw token is only ever emailed, never persisted, expires (`EMAIL_VERIFICATION_TOKEN_TTL_HOURS`, default 24h) and is single-use. New accounts start `is_verified=false`; login is never blocked for unverified users (the frontend shows a persistent "resend verification" banner instead, plus a Verified/Unverified badge on the Profile page) — a Google Sign-In account is `is_verified=true` immediately since Google has already verified that email. Two backends: `MAIL_BACKEND=console` (default; logs the link to the backend console — fine for local dev) and `MAIL_BACKEND=smtp` (`SMTPEmailService`, real delivery via `MAIL_SERVER`/`MAIL_PORT`/`MAIL_USERNAME`/`MAIL_PASSWORD`/`MAIL_USE_TLS`/`MAIL_FROM`, branded HTML+text email). Swapping in a provider-specific API (SES/SendGrid API, not their SMTP relay) later just means adding another `EmailService` implementation.
- **Rate limiting:** register/login/forgot-password/resend-verification are rate-limited per-IP via Flask-Limiter; `/auth/resend-verification` additionally enforces a per-account cap (`VERIFICATION_RESEND_MAX_PER_HOUR`, default 3/hour) so spreading requests across IPs can't bypass it — over the cap, the route still returns its normal 200 response without actually sending, so the cap itself can't be used to fingerprint whether an account exists.

## API reference (v1)

Base URL: `http://localhost:5000/api/v1`

### Health — `/health` (outside `/api/v1`, Phase 8)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | — | Deliberately unauthenticated liveness/readiness probe for Docker/an orchestrator. Reuses the same DB check the admin System Monitoring page shows (Phase 7). Returns `200` with `{"status": "ok", "database": {...}}` when the database is reachable, `503` with `{"status": "degraded", ...}` otherwise. |

### Auth — `/auth`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | — | Create an account. Body: `full_name, username, email, password, confirm_password` |
| POST | `/auth/login` | — | Body: `email, password, remember_me?` |
| POST | `/auth/refresh` | refresh cookie | Issues a new access token |
| POST | `/auth/logout` | — | Revokes current tokens, clears cookies |
| POST | `/auth/forgot-password` | — | Body: `email`. Always returns 200 (doesn't leak account existence) |
| POST | `/auth/reset-password` | — | Body: `token, password, confirm_password` |
| POST | `/auth/verify-email` | — | Body: `token` |
| POST | `/auth/resend-verification` | — | Body: `email` |

### Users — `/users`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/users/me` | access token | Current user profile |
| PUT | `/users/me` | access token | Update `full_name` / `username` |
| PUT | `/users/me/password` | access token | Body: `current_password, new_password, confirm_new_password` |

### URL Scanner — `/url`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/url/scan` | access token | Body: `{"url": "https://..."}`. Runs all 11 rules, persists the scan, returns the full report. Rate-limited (20/min). |
| GET | `/url/history` | access token | Query: `page, per_page, search, risk_level`. Paginated scan history for the current user. |
| GET | `/url/history/<id>` | access token | Full detail (report + rule breakdown) for one scan, scoped to the current user. |
| GET | `/url/stats` | access token | Dashboard aggregates: totals by risk level, average trust score, 5 most recent scans. |

`POST /url/scan` response shape:

```json
{
  "id": 12,
  "url": "https://example.com",
  "trust_score": 78,
  "risk": "Low Risk",
  "reasons": ["✔ Site does not use HTTPS — traffic is unencrypted."],
  "recommendations": ["Do not enter sensitive data over an unencrypted (HTTP) connection."],
  "rules": [{ "rule": "https_check", "label": "HTTPS", "triggered": true, "impact": -15, "severity": "medium", "message": "..." }, "... 10 more"],
  "scan_date": "2026-01-01T12:00:00Z"
}
```

### Email Scanner — `/email`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/email/scan` | access token | `multipart/form-data` with **either** `email_text` (pasted source) **or** `email_file` (`.eml`; `.msg` returns a clean 422 — see below). Rate-limited (15/min). |
| GET | `/email/history` | access token | Query: `page, per_page, search, risk_level`. `search` matches sender email, display name, or subject. |
| GET | `/email/history/<id>` | access token | Full detail for one scan, scoped to the current user. |
| GET | `/email/stats` | access token | Dashboard aggregates: totals by risk level, average trust score, 5 most recent scans. |

`POST /email/scan` response shape:

```json
{
  "id": 7,
  "sender_display_name": "PayPal Support",
  "sender_email": "support@mail-secure-paypal.com",
  "subject": "Urgent: Your Account Will Be Suspended",
  "trust_score": 12,
  "risk": "Dangerous",
  "reasons": ["✔ Display name references 'Paypal' but the sender domain is not an official Paypal domain."],
  "recommendations": ["Do not click the links in this email. Navigate to the official website directly instead."],
  "links": [{ "url": "http://paypa1-secure-login.com/verify", "trust_score": 67, "risk": "Suspicious" }],
  "attachments": [{ "filename": "invoice.pdf.exe", "is_dangerous": true, "reason": "Double extension disguises a dangerous '.exe' file as '.pdf'." }],
  "rules": ["... 10 rule results, same shape as the URL scanner"],
  "scan_date": "2026-01-01T12:00:00Z"
}
```

### QR Scanner — `/qr`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/qr/scan` | access token | `multipart/form-data` with `qr_image` (PNG/JPEG/WEBP, max 5 MB). Rate-limited (15/min). |
| GET | `/qr/history` | access token | Query: `page, per_page, search, risk_level`. |
| GET | `/qr/history/<id>` | access token | Full detail, scoped to the current user. |
| GET | `/qr/stats` | access token | Dashboard aggregates. |

### Scan Center — `/scans` (the unified abstraction layer)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/scans` | access token | Query: `page, per_page, scanner_type, risk_level, search, trust_score_min, trust_score_max, date_from, date_to, sort_by (scan_date\|trust_score), sort_dir`. Combines all three scanners' history via a SQL `UNION ALL` — no data is copied or migrated. |
| GET | `/scans/stats` | access token | Combined totals, risk distribution, per-type breakdown, recent scans, latest threats (Suspicious/Dangerous), top risks (lowest trust score). |
| GET | `/scans/<scanner_type>/<id>` | access token | Detail for one scan. `scanner_type` is `url`, `email`, or `qr`. |
| DELETE | `/scans/<scanner_type>/<id>` | access token | Deletes one scan from its underlying table. |
| POST | `/scans/bulk-delete` | access token | Body: `{"items": [{"scanner_type": "...", "id": ...}, ...]}` (max 100). |

The path uses a `(scanner_type, id)` compound key rather than a single numeric ID: each scanner keeps its own auto-incrementing `id` column in its own table (per this phase's explicit "keep previous tables, add an abstraction layer instead of migrating" guidance), so IDs collide across scanners — `url` scan #1 and `qr` scan #1 both exist. The compound key is the honest, unambiguous way to address a specific scan without inventing a fake unified ID space.

### Reports — `/reports`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/reports/<scanner_type>/<id>` | access token | Structured report: summary sentence, target, trust score/risk, findings (reasons + full rule breakdown), recommendations, and the underlying scan data. Computed on demand — not stored separately. |
| POST | `/reports/<scanner_type>/<id>/export` | access token | Body: `{"format": "pdf"}`. Always returns `501 Not Implemented` today — see `report_export_service.py`, the prepared (not yet implemented) export interface. Print and Share need no backend support: the frontend uses the browser's native `window.print()` and `navigator.share()`/clipboard APIs directly. |

### Dashboard — `/dashboard`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/dashboard` | access token | Per-user advanced widgets in one payload: `overall_security_score`, `threat_trend`, `recent_threat_timeline`, `weekly_activity`, `monthly_activity`, `scan_distribution`, `risk_distribution`, `most_dangerous_domains`, `most_common_keywords`, `most_common_scanner`, `threat_heatmap`, `average_scan_duration_ms`, `detection_accuracy` (honest placeholder), `recent_notifications`, `unread_notification_count`. |

### Profile — `/profile`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/profile` | access token | `{"user": ..., "stats": ...}` — extended `User` fields plus scan-derived stats (total/safe/dangerous scans, per-scanner-type counts, security score, recent activity), all computed via `unified_scan_service` — nothing re-queried or duplicated. |
| PUT | `/profile` | access token | Body: any of `phone, country, bio, avatar_url` (allow-listed — see Security notes below). Does **not** duplicate `/users/me`, which still owns `full_name`/`username`/password. |

### Settings — `/settings`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/settings` | access token | Returns (and lazily creates, on first access) the current user's `UserSettings` row. |
| PUT | `/settings` | access token | Body: any of `theme, language, timezone, notify_high_risk_url, notify_dangerous_email, notify_qr_threat, notify_weekly_summary, profile_visibility` (allow-listed). |
| GET | `/settings/sessions` | access token | Lists this user's active login sessions (audit-log layer over the existing JWT flow — see Security notes). |
| DELETE | `/settings/sessions/<id>` | access token | Revokes one session (reuses `auth_service.revoke_token`). |
| POST | `/settings/sessions/revoke-others` | access token | Revokes every session except the caller's current one. |
| DELETE | `/settings/account` | access token, rate-limited (3/min) | Body: `{"password": "..."}`. Deactivates the account (`is_active = false`, reusing the existing flag already enforced at login) and immediately revokes every session. |
| GET | `/settings/export` | access token | Always `501` today — prepared, unimplemented data-export placeholder. |

### Notifications — `/notifications`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/notifications` | access token | Query: `page, per_page, unread_only`. Auto-created by the URL/email/QR scan services when a scan crosses a risk threshold (Dangerous for URL/email, Suspicious+Dangerous for QR). |
| GET | `/notifications/unread-count` | access token | Powers the topbar bell badge. |
| PUT | `/notifications/<id>/read` | access token | Marks one notification read. |
| PUT | `/notifications/read-all` | access token | Marks every notification read. |
| DELETE | `/notifications/<id>` | access token | Deletes one notification. |

### Threat Intelligence — `/threats` (platform-wide, not per-user)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/threats` | access token | Known phishing domains (blacklist), suspicious domains, recently blocked domains, top targeted brands, most common keywords, attack categories, threat statistics, severity distribution, detection trends, blacklist overview, and `threat_feed_architecture` (see below). |
| GET | `/threats/domains` | access token | Query: `page, per_page, search, risk_level, sort_by (count\|last_seen\|domain), sort_dir`. Paginated, searchable, sortable feed merging scan-observed domains with the blacklist table. |
| GET | `/threats/export` | access token | Always `501` today — prepared, unimplemented export placeholder. |

Unlike every other Phase 5 resource, `/threats` deliberately isn't scoped to the current user — it aggregates across every account's scans, since "intelligence" means cross-user patterns, not personal history.

### Browser Extension — `/extension` (Phase 6)

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/extension/scan` | access token | Body: `{"url": "..."}`. Same validation and same `url_scanner.engine.scan_url` call as `/url/scan` — the only difference is nothing is written to the database (no `ScanHistory` row, no notification). Used only by the extension's Privacy Mode; the extension's default behavior calls the existing `/url/scan` endpoint unchanged. |

All authenticated requests rely on the `access_token` cookie set at login; mutating requests additionally require the `X-CSRF-TOKEN` header. The extension is a `chrome-extension://` origin, not the web app's origin, so it's additionally allow-listed via the `EXTENSION_ORIGINS` env var (see the Browser Extension section below) — CORS otherwise works identically to every other client of this API.

### Admin — `/admin/*` (Phase 7, requires the `admin` role)

Every route below is protected by `rbac.require_permission(...)` — a 403 (not a 404) is returned for an authenticated non-admin. There is deliberately no HTTP-reachable way to self-promote to admin.

| Method | Path | Permission | Description |
|---|---|---|---|
| GET | `/admin/dashboard` | `system.monitor` | System Overview: user counts, platform-wide scan stats, extension scan count, notification count, recent logins, system health. Cached 60s via the existing `@cacheable` placeholder. |
| GET | `/admin/users` | `users.view` | Query: `page, per_page, search, role`. All registered users. |
| GET | `/admin/users/<id>` | `users.view` | User + stats (reuses `user_profile_service`) + active sessions (reuses `session_service`). |
| GET | `/admin/users/<id>/activity` | `users.view` | Recent scan activity for one user. |
| POST | `/admin/users/<id>/deactivate` | `users.manage` | Sets `is_active=false` and revokes every session (reuses the existing account-deactivation path). |
| POST | `/admin/users/<id>/reactivate` | `users.manage` | Reverses deactivation. |
| POST | `/admin/users/<id>/reset-password` | `users.manage` | Always `501` today — prepared, unimplemented placeholder (no fake email is sent). |
| GET | `/admin/scans` | `scans.view` | Same filters as `/scans`, platform-wide (`user_id=None`) instead of scoped to the caller — the identical `unified_scan_service` UNION ALL query, generalized. |
| DELETE | `/admin/scans/<scanner_type>/<id>` | `scans.manage` | Delete any user's scan. |
| POST | `/admin/scans/bulk-delete` | `scans.manage` | Same shape as `/scans/bulk-delete`, platform-wide. |
| GET | `/admin/scans/export` | `scans.manage` | Always `501` today — same prepared-interface pattern as report/data export. |
| GET | `/admin/blacklist` | `scans.view` | Query: `page, per_page, search`. |
| POST | `/admin/blacklist` | `blacklist.manage` | Body: `domain, reason?`. Rejects full URLs (bare domain only) and duplicate domains (409). |
| DELETE | `/admin/blacklist/<id>` | `blacklist.manage` | Removes an entry. |
| POST | `/admin/blacklist/<id>/enable` | `blacklist.manage` | Re-enables a disabled entry. |
| POST | `/admin/blacklist/<id>/disable` | `blacklist.manage` | Disables without deleting — the URL scanner's blacklist rule already filters on `enabled=True`. |
| GET | `/admin/rules` | `rules.manage` | Query: `category` (`url`/`email`). Lazily seeds `DetectionRule` rows from the 21 real rule modules on first access. |
| PUT | `/admin/rules/<id>` | `rules.manage` | Body: `{"enabled": bool}`. Bumps `version` only on an actual state change. |
| GET | `/admin/audit-logs` | `audit.view` | Query: `page, per_page, action, user_id, status, search, date_from, date_to`. |
| GET | `/admin/system` | `system.monitor` | Request metrics (avg response time, error rate, requests in last 5 min), DB status, memory placeholder, uptime. |
| GET | `/admin/stats` | `system.monitor` | `{"overview": ..., "threat_intelligence": ...}` — composes `admin_dashboard_service.get_system_overview()` and `threat_intel_service.get_threat_intelligence_summary()` (the same data `/admin/dashboard` and `/threats` already expose) into one admin-gated payload for the Admin Threat Intelligence page. No new aggregation logic. |

### RBAC — roles & permissions

`app/rbac.py` defines four roles, but **only Admin is actually assignable today** — there is no UI or endpoint that grants Security Analyst or Viewer to anyone, per this phase's "implement the architecture now, only Admin is active" scope:

| Role | Permissions | Assignable today? |
|---|---|---|
| **Admin** | `users.view`, `users.manage`, `scans.view`, `scans.manage`, `blacklist.manage`, `rules.manage`, `audit.view`, `system.monitor` (all of them) | Yes (direct DB only — no self-promotion endpoint) |
| **Security Analyst** | `users.view`, `scans.view`, `blacklist.manage`, `rules.manage`, `audit.view` | No — reserved for a future phase |
| **Viewer** | `users.view`, `scans.view`, `audit.view` | No — reserved for a future phase |
| **User** (default) | none | — |

Adding Security Analyst/Viewer later is additive: grant the role somewhere and every `require_permission(...)`-guarded route already respects the matrix — no route code changes.

## URL detection rules & scoring

Every scan starts at 100 and each triggered rule subtracts (rules only ever add risk, never bonus points):

| Rule | Checks | Max impact |
|---|---|---|
| URL Length | Unusually long/short URLs | −15 |
| HTTPS | Missing HTTPS | −15 |
| SSL Certificate | Invalid/expired/unverifiable cert (real TLS handshake, only when HTTPS) | −20 |
| IP Address Host | Raw IP instead of a domain | −30 |
| Suspicious Keywords | login/verify/bank/wallet/paypal/etc. | −24 |
| Special Characters | `@` in host, excessive `%`, repeated `-`/`_`, smuggled `//` | −20 (per finding) |
| Subdomains | Unusually deep subdomain chains | −15 |
| Typosquatting | Levenshtein distance ≤2 from a known brand domain | −30 |
| Domain Age | RDAP lookup; recently registered / moderately aged / established | −15 |
| Blacklist | Exact match against the `blacklist_entries` table | −100 (forces Dangerous) |
| Redirect Chain | Long chains or a cross-domain final destination (SSRF-safe) | −20 |

Risk level thresholds: **90–100 Safe · 70–89 Low Risk · 40–69 Suspicious · 0–39 Dangerous**.

### Security & performance hardening

- **SSRF / DNS-rebinding:** every network-dependent rule resolves the hostname, validates the result isn't a private/loopback/link-local/reserved address, and then connects **directly to that validated IP** — never re-resolving the hostname at connect time. This closes the classic TOCTOU gap where a name resolves to something safe during validation and something internal (e.g. `169.254.169.254`, `127.0.0.1`) a moment later. TLS SNI and certificate-hostname verification still use the real hostname (via `server_hostname`/`assert_hostname`), so this doesn't weaken certificate checking. The redirect-chain rule re-validates and re-pins on every hop.
- **Input hardening:** the URL schema rejects control characters, embedded spaces, and unparseable input with a clean 422 instead of risking an unhandled exception.
- **Concurrent, time-boxed scanning:** the three network-bound rules (SSL, domain age, redirects) run in parallel via a thread pool instead of stacking their latencies serially, bounded by an 8-second overall deadline — one slow or hanging target degrades to a graceful "check timed out" for that rule rather than blocking the whole scan (or a whole worker process) indefinitely. A bug or unexpected exception in one rule is contained the same way and doesn't fail the scan.
- **Storage:** `scan_result`/`analysis_details` use `JSONB` on Postgres (plain `JSON` on SQLite in tests) for more compact, indexable storage.
- **Reverse proxies:** `TRUST_PROXY_HEADERS=true` enables Werkzeug's `ProxyFix` so rate limiting keys off the real client IP (`X-Forwarded-For`) instead of the proxy's — off by default, since enabling it without a trusted proxy in front would let clients spoof their own rate-limit identity.

## Email detection rules & scoring

Same 100-point, subtract-only scoring model as the URL scanner.

| Rule | Checks |
|---|---|
| Sender Analysis | Missing/malformed sender address; a free-provider address (Gmail, Yahoo, ...) whose display name claims to be an organization |
| Display Name Impersonation | Display name names a specific known brand, but the sender domain isn't that brand's real domain (extensible registry in `brands.py`) |
| Subject Analysis | Phishing-lure phrases in the subject line (urgent, verify, suspended, lottery, ...) |
| Greeting Analysis | Generic greetings ("Dear Customer/User/Client") instead of a real name |
| Urgency Detection | Pressure language ("act now", "within 24 hours", "final warning") |
| Threat Language | Consequence language ("account suspension", "security breach", "verify your identity") |
| Link Analysis | Every link in the email, classified via the URL scanner's `quick_classify` — no network calls, capped at 20 links per email |
| Attachment Analysis | Dangerous extensions (`.exe`, `.js`, `.scr`, ...) and double-extension disguises (`invoice.pdf.exe`) |
| HTML Analysis | Embedded `<script>`/`<form>` tags, hidden/invisible elements, excessive external resources, obfuscated encoding |
| Grammar Heuristics | Light-touch, low-weight signals (repeated punctuation, ALL-CAPS ratio, stock scam phrasing) — deliberately capped so it's never a major factor |

### Security

- **No disk I/O:** pasted text and uploaded files are parsed entirely in memory (Python's stdlib `email` package) and discarded — never written to disk, so there's no path-traversal surface from a filename.
- **Attachment content is never decoded** — only the filename/content-type metadata the rules need, which sidesteps decompression-bomb-style resource exhaustion from attachment payloads entirely.
- **Size limits, layered:** a hard WSGI-level `MAX_CONTENT_LENGTH` (8 MB) rejects oversized requests before they're buffered into memory at all; the email endpoint additionally enforces its own tighter limits (200 KB pasted text, 5 MB file upload) for a clear, application-level error message.
- **Input hardening:** pasted text is rejected if it contains control characters; uploaded filenames are extension-checked (`.eml`/`.msg` only) before anything is parsed.
- **`.msg` (legacy Outlook binary format):** not parsed yet — returns a clear 422 rather than silently failing or attempting something fragile. `email_scanner/msg_parser.py` is the prepared integration point for adding real support (e.g. via `extract-msg`) later without touching any other code.
- **Malformed MIME:** Python's `email` package is tolerant by design (parse problems become `.defects`, not exceptions) — parsing is still wrapped defensively so a pathological input degrades to an empty/partial result instead of a 500.

## QR content types & handling

| Content type | Handling |
|---|---|
| Website URL | Full reuse of the URL scanner's `scan_url()` |
| Email (`mailto:`) | Full reuse of the email scanner's `analyze_email()` |
| Phone (`tel:`) | Format validation + known premium-rate pattern detection |
| SMS (`sms:`/`smsto:`) | Message body checked with the email scanner's urgency/threat-language rules |
| WiFi (`WIFI:...`) | SSID/security/hidden shown; password never exposed, even in "raw content" view |
| Crypto wallet | Format validation (BTC/ETH/LTC/DOGE/TRON/XRP patterns) + standard caution — no blockchain lookup |
| Plain text | Displayed safely, no analysis needed |
| Unknown / undecodable | Treated as Suspicious by default (can't be positively classified as safe) |

### Security

- **No disk I/O:** images are decoded entirely in memory (Pillow + pyzbar) and discarded.
- **Image validation:** `Image.verify()` checks structural integrity before decoding; format is restricted to PNG/JPEG/WEBP; Pillow's built-in `MAX_IMAGE_PIXELS` guard protects against decompression-bomb-style oversized images.
- **Layered size limits:** the same hard WSGI-level `MAX_CONTENT_LENGTH` backstop as the email scanner, plus a 5 MB application-level limit with a clear error message.
- **Never renders HTML:** decoded QR content (including totally unclassified/unknown content) is only ever rendered as plain text in React, which auto-escapes it — `dangerouslySetInnerHTML` is not used anywhere in the QR result UI.

## Phase 5: Dashboard Intelligence, Threat Intelligence, Profile, Settings & Notifications

Everything in this phase is computed from the three existing scan tables, the existing `blacklist_entries` table, or the existing unified-scan aggregate — **no new detection logic and no fake data**. Where real data doesn't exist yet (detection accuracy, live threat feeds, data/threat-intel export), the API returns an honestly-labeled placeholder instead of a fabricated value.

- **`scan_analytics.py`** factors out the "tally keyword/domain/brand rule hits across scan history" logic shared by `dashboard_service.py` (per-user, `user_id` required) and `threat_intel_service.py` (platform-wide, `user_id=None`) — one implementation, two callers, no duplicated business logic.
- **`ThreatFeedProvider`** (`threat_intel_service.py`) is the same "prepare architecture, don't fake the feature" interface pattern already used for `EmailService`/`DomainAgeProvider`/`ReportExporter`: an abstract base plus one concrete `InternalThreatFeedProvider` backed by the platform's own blacklist + scan history. A future live feed (PhishTank, OpenPhish, ...) is a second provider implementation away — no call sites change.
- **Caching placeholder:** `app/utils/cache.py`'s `@cacheable(ttl_seconds=...)` is a no-op decorator marking where a real cache (Redis, etc.) should sit around the most expensive platform-wide aggregation (`threat_intel_service.get_threat_statistics`) — documented, not implemented, per this phase's explicit scope.
- **Real, measured scan durations:** `app/utils/timing.py`'s `Stopwatch` times each scan in `scan_service`/`email_scan_service`/`qr_scan_service` and writes to a new nullable `duration_ms` column, populated only going forward — "Average Scan Duration" averages non-null rows and is never backfilled/fabricated for older scans.
- **Session tracking** (`UserSession` / `session_service.py`) is an audit-log layer *on top of* the existing JWT issuance flow, not a redesign of it: `auth_service.issue_token_pair` now also mints a `sid` claim shared by the access+refresh token pair (since the refresh cookie itself is scoped to `/auth/refresh` only and is never present on `/settings/sessions` requests); revocation still goes through the one existing `TokenBlocklist` mechanism `/auth/logout` already used.
- **Mass-assignment prevention:** every Phase 5 update endpoint (`/profile`, `/settings`) uses an explicit allow-list tuple (`UPDATABLE_PROFILE_FIELDS`, `UPDATABLE_FIELDS`) plus marshmallow schemas that reject unknown fields by default — never a blind `for k, v in data.items(): setattr(...)`.
- **Notifications** are created by one policy table (`notification_service._SCAN_NOTIFICATION_RULES`) consulted from a single hook (`notify_scan_result`) called after each of the three scan services persists a result — the scan services themselves know nothing about notification rules.
- **Theme setting — scope decision:** Phases 1–4 were built against one fixed dark palette with colors hardcoded per-component (no light-mode CSS existed anywhere). Re-skinning every already-built screen for a full light mode would mean touching dozens of completed files — a redesign, which is explicitly out of scope. Instead, the theme preference is fully real (persisted server-side, applied instantly via a `data-theme` attribute, responsive to OS `prefers-color-scheme` when set to "system"), and light-mode CSS covers the shared primitives every page already composes from (`glass-card`, `input-field`, `btn-secondary`, and the `text-slate-*` utility scale, scoped to `<main>` so the intentionally-still-dark sidebar/topbar are untouched). The overall page canvas and sidebar remain dark in "light" mode — a deliberate, documented boundary (see `frontend/src/lib/theme.ts`), not an oversight.

## Phase 6: Browser Extension

A Manifest V3 extension in `extension/`, shipped as plain JS/HTML/CSS with **no bundler and no build step** — every file is exactly what the browser loads. It reuses the platform's existing URL Security Engine and auth system rather than reimplementing anything:

```
extension/
├── manifest.json
├── icons/                          # generated via generate_icons.py (Pillow), brand-matched shield+check
├── src/
│   ├── shared/
│   │   ├── browser-api.js          # chrome/browser shim — Firefox readiness, no polyfill dependency
│   │   ├── constants.js            # risk levels/colors, default settings, cache/rate-limit tuning
│   │   ├── storage.js              # chrome.storage wrapper — settings (sync), cache/stats (local)
│   │   └── api-client.js           # fetch + cookie/CSRF auth + 401-refresh-retry, mirrors frontend/src/lib/api.ts
│   ├── background/background.js    # service worker: navigation detection, scan orchestration, badge, notifications
│   ├── content/
│   │   ├── content.js              # asks background for a verdict; renders the warning overlay if blocking
│   │   └── warning-styles.js        # CSS for the overlay's closed shadow root (can't be a manifest-injected .css file)
│   ├── popup/                      # popup.html/js/css — current site's trust score, risk, reasons, quick actions
│   └── options/                    # options.html/js/css — protection/notifications/threshold/theme/privacy/stats
└── tests/                          # Vitest + jsdom; a fake chrome.* mock stands in for the real browser APIs
```

**No duplicate detection logic:** the extension never scores a URL itself. By default it calls the *exact same* `POST /url/scan` endpoint the web dashboard's URL Scanner page calls, so an automatically-scanned page shows up in the user's real Scan Center/dashboard history exactly like a manual scan would. The one new backend route, `POST /extension/scan` (see the API reference above), exists solely for Privacy Mode and calls the identical `url_scanner.engine.scan_url()` function — it just skips the `ScanHistory` write. Everything else (the rule engine, trust score, risk thresholds, reasons/recommendations) is 100% Phase 2 code, untouched.

**Auth — reused, not reimplemented:** the extension has no login screen. It rides the same httpOnly `access_token`/`refresh_token` cookies the web app sets when the user logs in via the dashboard in the same browser, and reads the CSRF double-submit cookies via `chrome.cookies` (service workers have no `document.cookie`). `api-client.js`'s 401 → refresh → retry-once flow mirrors `frontend/src/lib/api.ts`'s axios interceptor line for line. If the user isn't logged in, the popup shows a "Sign in required" state with a button that opens the dashboard's login page — it does not attempt to authenticate on its own.

**Manifest permissions** (each justified by one feature, not requested speculatively):

| Permission | Why |
|---|---|
| `storage` | Settings (sync) + scan-result cache and local stats (local). |
| `notifications` | Dangerous/suspicious/failed-scan/connection alerts (Part 7). |
| `alarms` | Periodic cache cleanup that survives service-worker suspension — no `setInterval`, which doesn't. |
| `webNavigation` | Reliable navigation detection, including SPA `pushState` routes (`onHistoryStateUpdated`), which `tabs.onUpdated` alone misses. |
| `tabs` | Read the active tab's URL for the popup and per-tab badge/state. |
| `cookies` | Read the CSRF cookies from the background service worker (no DOM access there). |
| `host_permissions: http(s)://*/*` | Required for the content script to run on every page (the core feature — real-time protection inherently needs to see every visited URL) and for `tabs.query()` to return `.url`. |

Deliberately **not** requested: `scripting` (content scripts are static, declared in the manifest, never dynamically injected) and any wildcard `chrome-extension://` CORS allowance on the backend (see `EXTENSION_ORIGINS` below) — a blanket allowance would let *any* other installed extension ride the user's CyberShield session cookie.

**Warning UI security:** the full-page warning (Part 3) is rendered inside a **closed shadow root** (`attachShadow({mode: "closed"})`), not injected directly into the page DOM. A closed shadow root cannot be reached from the host page's own JS via `element.shadowRoot` — the page can't detect, inspect, restyle, or rip out the warning once it's shown. "Continue Anyway" is remembered per-host for the current browsing session (not persisted forever) so revisiting the same warning doesn't nag on every link click.

**Performance (Part 9):**
- Scan results are cached per-URL for 5 minutes (`CACHE_TTL_MS`) — revisiting or re-rendering the same page never re-scans it.
- Concurrent requests for the same not-yet-cached URL (the `webNavigation` listener and the content script both ask at once) are de-duplicated into a single in-flight API call.
- A client-side sliding-window rate limiter (15 req/min, under the backend's own 20/min limiter) backs off *before* the server would ever reject a request.
- Failed scans retry with exponential backoff (`RETRY_BASE_DELAY_MS * 2^attempt`, capped at `RETRY_MAX_ATTEMPTS`), except on 401/422 where retrying can never succeed.
- All scanning happens in the background service worker — the content script only renders whatever verdict it's given, so a slow or failed check never blocks page rendering.

**Configurable Danger Threshold:** the API's own Safe/Low Risk/Suspicious/Dangerous labels come from the backend's fixed 90/70/40 score thresholds. The extension's "Danger Threshold" option (default 39, matching the backend's Dangerous cutoff exactly) is a *separate*, user-adjustable line compared directly against `trust_score` — raising it makes the extension warn more readily than the API's own Dangerous/Suspicious boundary. This is what makes the slider on the options page actually do something, rather than being cosmetic.

**Privacy Mode vs. Statistics Collection** — two independent, honestly-scoped toggles: Privacy Mode controls whether scans reach the server as persisted (`/url/scan`) or ephemeral (`/extension/scan`) requests; Statistics Collection controls only the small local counters (`chrome.storage.local`) shown on the options page (scans run, threats blocked) — it never affects what is or isn't sent to the API.

**Browser compatibility:** built and tested against Chrome/Edge (Manifest V3, `chrome.*`). Firefox support is architected for but not yet tested in a real Firefox: `browser-api.js` prefers a `browser` global (Firefox's native Promise-based namespace) over `chrome` automatically, and every other file calls through that shim rather than `chrome.*` directly — porting means verifying Firefox's MV3 support for `content_scripts`/`webNavigation`/service-worker-as-event-page, not rewriting extension logic.

**Testing:** `cd extension && npm install && npm test` (Vitest + jsdom) — 65 tests: shared-module unit tests (constants, storage cache/TTL/eviction, api-client CSRF/401-refresh/error-mapping), background service-worker integration tests (message handling, caching, rate limiting, retry, graceful-failure) driven through its real `chrome.runtime.onMessage` listener against a fake `chrome.*`, content-script tests (shadow-root overlay rendering, Continue Anyway/Go Back/View Report, session overrides, live updates — verified via intercepting `attachShadow` at creation time so the *closed* shadow root's real security property isn't weakened just for testability), popup-state tests, a manifest/permissions regression suite, and dedicated performance tests (cache-hit-avoids-fetch, concurrent-request dedup, rate-limiter window reset). Two real bugs were caught and fixed by this suite before it ever touched a real browser: a bare top-level `const` in `warning-styles.js` that (correctly, per how the manifest loads multiple content-script files as separate top-level script scopes) wasn't visible from `content.js`, and a missing `settings` argument on the cache-hit path that crashed `isBlockingResult`. The extension was then also load-tested unpacked in real Chromium (service worker registration, popup, and options page all verified with zero console errors) as a final sanity check beyond the mocked test suite.

## Phase 7: Enterprise Security + Administration Platform

An admin dashboard and supporting security/monitoring infrastructure, built entirely additively on top of Phases 1–6: no detection engine was rewritten, no existing table was migrated away from, and every previous route/response shape is unchanged.

**Frontend:** a parallel route tree at `/admin/*` (`AdminRoute` guard → `AdminLayout`/`AdminSidebar`, styled distinctly from the main dashboard shell) with 8 pages: System Overview, Users (+ per-user detail), Scans, Blacklist, Rule Management, Audit Logs, and System Monitoring. An "Admin Panel" link appears in the regular dashboard sidebar only when `user.role === "admin"`.

- **RBAC, not just a role flag:** `role` has been present in the JWT since Phase 1 but nothing ever checked it before this phase. `app/rbac.py` adds a `PERMISSIONS` matrix and a self-contained `require_permission(permission)` decorator (includes its own `@jwt_required()`) used by every admin route. Four roles are defined (`Role.ALL`) but only Admin is wired to anything today — see the RBAC table above.
- **Audit logging, additive:** `AuditLog` (new table) + `audit_service.log_action()` is called from existing route handlers — login/logout, profile/settings updates, report generation, scan deletion, extension scan events — as one extra line appended after the existing success/failure path. No handler's core logic changed.
- **Rule enable/disable without touching the detection engines:** `DetectionRule` (new table, seeded from the 21 real rule modules' own `label`/severity literals) plus `rule_registry_service.filter_enabled_rules(category, rules, rule_name)` — a thin filter called by `url_scanner/engine.py` and `email_scanner/engine.py` immediately before their existing rule-iteration loop. The rule modules' `evaluate()` functions are never touched; only which modules get called is filtered. A missing/un-seeded `DetectionRule` row defaults to *enabled*, so a fresh test database (built via `db.create_all()`, which skips data migrations) never silently disables every rule. **Known, accepted tradeoff:** this queries `DetectionRule` fresh on every scan rather than caching — an earlier `flask.g`-based cache was removed after it caused stale reads (see Errors & fixes below); per this phase's "avoid premature optimization" instruction, it's left uncached until proven to matter.
- **Admin-wide scan queries via generalization, not duplication:** `unified_scan_service.py`'s functions (`get_unified_scans`, `get_scan_record`, `delete_scan`, `bulk_delete_scans`, `get_unified_stats`) had their `user_id: str` parameter widened to `user_id: str | None` — `None` means platform-wide. The same `UNION ALL` SQL now also joins `User` to expose `user_id`/`username` for admin display. One implementation serves both the per-user Scan Center (unchanged behavior — a real `user_id` is always passed) and the new admin-wide Scans view (`user_id=None`) — the same pattern Phase 5 already established for `dashboard_service`/`threat_intel_service`.
- **Scan source attribution:** `source` (`"web"` | `"extension"`) added to `ScanHistory`/`EmailScanHistory`/`QRScanHistory`, set via `app/utils/client.py`'s `detect_source(request)`, which reads an explicit `X-CyberShield-Client: extension` header the extension's `api-client.js` now sends — never inferred from User-Agent or other heuristics.
- **System monitoring:** `app/middleware/request_metrics.py` records `{path, method, status, duration_ms, at}` for every request in a bounded in-memory `deque(maxlen=2000)` — no persisted metrics store, resets on process restart, documented as such on the System Monitoring page.

### Security review (Part 8)

Phase 1 already shipped `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, a restrictive CSP (`default-src 'none'; frame-ancestors 'none'`), and HSTS (gated on `not app.debug`). This phase's review added two more and deliberately left two choices as-is after reasoning through the risk:

- **Added `Cross-Origin-Opener-Policy: same-origin`** — isolates the browsing context group; safe, since it only affects `window`/opener relationships, not fetches.
- **Added `Cross-Origin-Resource-Policy: cross-origin`** — deliberately **not** `same-origin`. The frontend is served from a different origin than the API, and the browser extension's legitimate, CORS-approved fetches come from a `chrome-extension://` origin; CORP is enforced independently of CORS, so `same-origin` would silently break both without any CORS error to explain why. `cross-origin` is the correct choice given this platform's actual architecture (documented at length in `middleware/security_headers.py`).
- **JWT/cookie config reviewed, unchanged:** httpOnly cookies, double-submit CSRF, bcrypt password hashing, and the `TokenBlocklist` revocation flow (Phase 1) were already sound; RBAC (this phase) is layered on top rather than replacing any of it.
- **File upload validation reviewed, unchanged:** the email/QR scanners' existing size limits, content-type/extension checks, and in-memory-only decoding (Phases 3–4) were already correct; no gaps were found that needed fixing this phase.
- **Mass-assignment prevention:** admin mutation endpoints follow the same explicit allow-list pattern as `/profile`/`/settings` — `AdminBlacklistAddSchema`/`AdminRuleToggleSchema`/etc. in `app/schemas/admin.py` reject unknown fields by default.

### Performance review (Part 9)

Per this phase's "avoid premature optimization, only optimize proven bottlenecks" instruction, no speculative indexes or query rewrites were made. What was verified:

- `test_performance_rule_registry.py` confirms `filter_enabled_rules` scales linearly (one query per category per scan), not quadratically, and that removing the earlier `flask.g` cache didn't reintroduce an N+1 pattern across a batch of link classifications.
- The admin-wide `unified_scan_service` queries reuse the exact same indexed columns (`user_id`, `scan_date`, `trust_score`) the per-user Scan Center already relied on — no new indexes were needed since `user_id=None` just omits a `WHERE` clause rather than changing the query shape.
- `admin_dashboard_service.get_system_overview()` reuses the existing `@cacheable(ttl_seconds=60)` no-op-today placeholder from Phase 5, marking the same intended cache point a real backend cache would sit at.

### Errors & fixes worth knowing about

- **`flask.g` is application-context-scoped, not request-scoped.** An initial version of `rule_registry_service.py` cached disabled-rule names in `flask.g` to avoid a query per link during email scans. It caused a real bug: after disabling a rule via `PUT /admin/rules/<id>`, a subsequent scan still ran it — because this project's own test fixture wraps a whole test in one `app.app_context()`, and Flask does not push a new app context for each nested request context inside an already-active one, so `g` silently persisted across what looked like separate requests. Fixed by removing the cache entirely and querying fresh every call — a deliberate, documented tradeoff, not an oversight.
- **Migration on non-empty tables:** Alembic autogenerate produced `nullable=False` columns with no default for `blacklist_entries.enabled` and the three `*.source` columns — invalid against Postgres tables that already had rows. Manually patched the generated migration with `server_default=sa.true()` / `server_default='web'`.

## Phase 8 (v1.0): Production Polish + Deployment Preparation

The final phase — no new detection logic, no new database tables, no API removed or redesigned. Everything below is presentation, hardening, and deployment tooling on top of the fully-functional Phases 1–7 platform.

**Landing page:** `HomePage.tsx` now composes 13 sections from `components/landing/`: Hero, animated Stats (a small `AnimatedCounter` counts up on scroll into view — no new dependency, just `requestAnimationFrame` gated by framer-motion's `useInView`), Product Overview, Features, How It Works, a tabbed URL/Email/QR Scanner showcase (illustrative example scans, explicitly labeled as such — not live), a Browser Extension showcase, a Threat Intelligence capabilities section, a Dashboard preview (illustrative, explicitly labeled "Preview"), Testimonials (**explicitly labeled "Demo testimonials — illustrative personas for demonstration purposes"** — no fabricated real reviews), an accessible FAQ accordion, a Contact section (an honest `mailto:` link to a clearly-labeled placeholder address — no fake contact form that submits nowhere), and a closing CTA. The footer gained working section links plus two new real pages, `/privacy-policy` and `/terms-of-service`, written in plain language for what this project actually stores and does (not disconnected legal boilerplate).

**Responsiveness — one genuine bug found and fixed:** automated viewport testing (375/768/1440px) caught real horizontal overflow on `/admin/rules` at mobile width. Root cause: `DashboardLayout`/`AdminLayout`'s content column is a `flex-1` flex item without `min-width: 0`, so a wide table inside — despite its own `overflow-x-auto` wrapper — forced the whole flex item (and thus the page) wider than the viewport, a classic flexbox `min-width: auto` trap. Fixed with one `min-w-0` class in both layouts; verified overflow-free afterward at all three breakpoints across every dashboard/admin page tested.

**Accessibility:** every interactive element now gets a visible `:focus-visible` ring (`index.css`) — previously only form inputs had one. All 7 paginated list pages' previously icon-only Previous/Next buttons gained `aria-label`s (a real, repeated gap — screen readers previously announced only "button"). Decorative mobile-sidebar backdrop overlays are now `aria-hidden`. The FAQ accordion uses proper `aria-expanded`/`aria-controls`/`role="region"` wiring rather than a plain show/hide `<div>`.

**Performance:** every dashboard and admin page is now `React.lazy`-loaded (`App.tsx`) behind a `Suspense` boundary using the existing `LoadingScreen` — the public landing page and auth flows no longer pay for the weight of pages reachable only after login. Verified via a real production build: the pages are split into their own chunks (e.g. `DashboardHomePage` 19KB, `AdminOverviewPage` 8.5KB) rather than bundled into one monolithic file. Image optimization wasn't applicable — the entire frontend has always been built from hand-rolled SVG/CSS (no charting library, no raster images), a pre-existing, deliberate choice, not new work this phase.

**Production readiness:** `/health` (outside `/api/v1`) now performs a real, cheap DB connectivity check (reusing Phase 7's `get_database_status()`) and returns `503` if the database is unreachable, instead of always claiming "ok" — this is what a real Docker/orchestrator healthcheck should probe. Every mutating `/admin/*` route (deactivate/reactivate user, delete/bulk-delete scan, add/remove/enable/disable blacklist entry, toggle rule) now carries the same `@limiter.limit(...)` pattern already used elsewhere in the codebase — previously, an authenticated admin session had no throttle on any admin action at all.

**Deployment preparation (not deployed):** `backend/Dockerfile.prod` (gunicorn, 4 workers, non-root user, container `HEALTHCHECK` hitting `/health`) and `frontend/Dockerfile.prod` (multi-stage: `vite build` → static files served by `nginx.conf`, with SPA fallback routing and long-cache headers for hashed assets) were both **built and smoke-tested** — not just written: the backend image was run standalone and `/health` was confirmed reachable; the frontend image was run standalone and confirmed to serve both `/` and a deep client-side route (`/dashboard/profile`) with the correct `index.html` fallback. `docker-compose.prod.yml` wires both together (no bind-mounted source, `FLASK_ENV=production`, container healthchecks, no published Postgres port) and `.env.production.example` documents every production-relevant setting — including two honest, undismissed caveats: the in-memory rate limiter and in-memory request-metrics ring buffer are both **per-process**, so a real multi-worker/multi-replica deployment needs a shared store (e.g. `RATELIMIT_STORAGE_URI=redis://...`) to get accurate limits — documented as a known limitation rather than silently ignored or over-engineered away.

**Final security review findings:** a full pass across RBAC, JWT/cookie config, CORS, CSRF, SSRF protections, SQL-injection surface (grepped for raw/interpolated SQL — none found; every query goes through the SQLAlchemy Core/ORM builder), and XSS surface (grepped for `dangerouslySetInnerHTML` — none found) turned up one genuine, fixed gap: **no rate limiting on any `/admin/*` mutation** (see above). Everything else reviewed was already sound from prior phases and was left untouched, per this phase's "only fix genuine issues" scope.

## Deployment (production)

This section documents how the prepared production stack works — it has been build-tested (see above) but **was not deployed** by this phase, per its explicit scope.

1. Copy `.env.production.example` to `.env.production` and fill in real secrets (`SECRET_KEY`, `JWT_SECRET_KEY`, `POSTGRES_PASSWORD`), your real domain (`FRONTEND_ORIGIN`, `FRONTEND_BASE_URL`, `VITE_API_BASE_URL`), and your extension's real id(s) if you're shipping it (`EXTENSION_ORIGINS`).
2. Build and start the production stack:
   ```bash
   docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
   ```
3. Run migrations once, explicitly (never implicit on container start, so a restart never silently re-runs them):
   ```bash
   docker compose -f docker-compose.prod.yml --env-file .env.production run --rm backend flask --app wsgi.py db upgrade
   ```
4. Point a real reverse proxy/TLS terminator (nginx, Caddy, an ALB, Cloudflare, ...) at the `frontend` (5173) and `backend` (5000) containers, and set `TRUST_PROXY_HEADERS=true` only once one is actually in front — otherwise rate limiting can be spoofed via `X-Forwarded-For`.
5. Before real users rely on it: set `MAIL_BACKEND=smtp` and fill in `MAIL_SERVER`/`MAIL_PORT`/`MAIL_USERNAME`/`MAIL_PASSWORD`/`MAIL_USE_TLS`/`MAIL_FROM` (password reset and email verification still only log to console under the `MAIL_BACKEND=console` default), and consider `RATELIMIT_STORAGE_URI=redis://...` if you're running more than one backend worker/replica (see the caveat above).

## Testing

- **Backend:** `docker compose run --rm backend pytest` — 360 tests, all passing. Phase 8 adds 2 (to the 358 from Phases 1–7, all still passing unmodified): the DB-aware `/health` endpoint.
- **Extension:** see the Phase 6 section above — 66 Vitest tests, unchanged and still passing, plus a real-Chromium unpacked-extension load smoke test.
- **Manual/browser (Phase 5):** register → dashboard (now showing the new Advanced Intelligence section — security score gauge, threat trend, weekly/monthly activity, risk distribution, heat map, most-dangerous-domains, most-common-keywords, quick actions — alongside the unchanged Phase 1–4 sections) → topbar notification bell + full Notifications page (mark read/all-read/delete) → Profile page (extended fields save and persist) → Settings page (theme toggle actually flips `data-theme` and persists across reload; active-session list; account deactivation blocks future login) → Threat Intelligence Center (platform-wide stats, domain feed search/filter/sort/pagination). Caught and fixed two real bugs during this pass: (1) an escaped-selector CSS rule with a circular `@apply text-slate-600` self-reference broke the entire stylesheet compile (500 error, blank page) — removed; (2) a second escaped-selector block for opacity-based background utilities was silently mis-parsed by PostCSS and bled into unrelated `.glass-card` rules — removed in favor of the simpler, already-proven `.glass-panel`/`.glass-card` overrides.
- **Manual/browser (Phase 7):** an account was promoted to `admin` via direct DB mutation (there is deliberately no API path for this) and driven through a real Chromium instance: login → "Admin Panel" sidebar link appears and navigates to `/admin` → all 7 admin pages (System Overview, Users, Scans, Blacklist, Rules, Audit Logs, System Monitoring) render with real data and zero console errors → user-detail drill-down → a rule was toggled off then back on (`enabled: true → false → true`, confirmed via the UI switch state) → a blacklist domain was added then removed. Separately verified the RBAC guard: a non-admin account sees no "Admin Panel" link, and direct navigation to `/admin` and `/admin/users` both client-side redirect to `/dashboard`.
- **Manual/browser (Phase 8):** the new landing page was driven end-to-end in real Chromium — every new section renders (Overview, Scanner showcase tab-switching, Extension showcase, Threat Intelligence, Dashboard preview, Testimonials, FAQ accordion open/close, Contact, both new legal pages) with zero console errors. Automated multi-viewport testing (375px/768px/1440px) across the landing page, auth pages, and — logged in — the dashboard and admin areas confirmed no horizontal overflow anywhere (this is what caught the `/admin/rules` flexbox bug fixed above). The full register → dashboard flow was re-verified working end-to-end after all Phase 8 changes. Both `Dockerfile.prod` images were built and smoke-run standalone (see the Deployment section above) as part of this pass, not left as unverified paper artifacts.

## Frontend routing note

Per this phase's "keep existing functionality, add an abstraction layer" guidance, the Phase 3 tabbed `HistoryPage` (URL Scans / Email Scans tabs) at `/dashboard/history` is **unchanged** and still reachable from the sidebar. The new unified Scan Center is a separate, additional page at `/dashboard/scan-center`, linked from the sidebar and from the new dashboard "Open Scan Center" / "View all" links. Nothing was removed or replaced — the unified view was added alongside the existing one.

## Roadmap

A dedicated Reports dashboard is still a placeholder in the sidebar (marked "Soon"). The admin panel is now implemented (Phase 7) — blacklist management, rule enable/disable, and audit logs all have a real UI instead of direct DB access. `.msg` file parsing (`email_scanner/msg_parser.py`) and PDF report export (`report_export_service.py`) are prepared-but-unimplemented integration points. As of Phase 8, CyberShield is **v1.0** — a complete, production-hardened, deployment-ready thesis/portfolio platform; see below for what's still honestly out of scope.

**Added in Phase 5, still placeholders by design:**

- **Detection Accuracy** (Dashboard): requires labeled ground-truth data (confirmed true/false positives) that CyberShield doesn't collect yet — returns `{"available": false, "message": "..."}` rather than a fabricated number.
- **Data export** (`/settings/export`) and **Threat Intelligence export** (`/threats/export`): always `501` today, same prepared-interface pattern as PDF report export.
- **Live external threat feed**: `ThreatFeedProvider` is ready for a second implementation (PhishTank/OpenPhish/etc.); only `InternalThreatFeedProvider` (the platform's own data) exists today.
- **Real caching**: `@cacheable` in `app/utils/cache.py` marks the intended cache point around the platform-wide threat-statistics query; it's a no-op until a real backend (Redis, etc.) is wired in.
- **Full light-mode re-skin**: the theme setting is fully functional and persisted, but only the shared UI primitives and page text re-theme — the dark navy sidebar/topbar/canvas is a deliberate, documented scope boundary (see the Phase 5 architecture section above), not an unfinished feature.

**Added in Phase 6, still placeholders by design:**

- **Firefox**: the `browser-api.js` shim and Promise-based API usage throughout are Firefox-ready, but the extension has only been built and tested against Chrome/Edge — porting is verification work, not a rewrite.
- **Chrome Web Store / Edge Add-ons packaging and publishing**: out of scope per this phase's instructions (no deployment work); the extension currently only runs as an unpacked/developer-mode install.
- **Extension-side "Report a false positive/negative"**: not implemented — the popup's "View Report" links to the same report the web dashboard already generates rather than adding a second feedback mechanism.
- **Multiple simultaneous CyberShield accounts**: the extension, like the web app, assumes one logged-in session per browser profile.

**Added in Phase 7, still placeholders by design:**

- **Security Analyst / Viewer roles**: `app/rbac.py` defines the full permission matrix for both, but no UI or endpoint grants either role to a user yet — only Admin is assignable today, per this phase's explicit scope.
- **Admin-initiated password reset**: `POST /admin/users/<id>/reset-password` always returns `501` — no fake reset email is sent.
- **Scan export (admin)**: `GET /admin/scans/export` always returns `501`, same prepared-interface pattern as report/data/threat-intel export.
- **Custom/user-authored detection rules**: `DetectionRule` currently only tracks the 21 existing built-in rules' metadata (enable/disable, severity, version); the architecture is ready for user-authored rules later, but authoring one isn't possible yet.
- **Memory usage** (System Monitoring): returns `{"available": false, "message": "..."}` rather than a fabricated number — no `psutil`-style dependency has been added yet.
- **Real request-metrics persistence**: `request_metrics.py`'s bounded in-memory `deque` resets on every process restart/deploy; a durable metrics store (Prometheus, etc.) is future work, not implemented here.

**Added in Phase 8 (v1.0), still honest limitations:**

- **This was not actually deployed.** Per this phase's explicit scope, `docker-compose.prod.yml` was built and smoke-tested locally, not pointed at a real server, domain, or TLS certificate.
- **In-memory rate limiting and request metrics are per-process**: with more than one gunicorn worker or replica behind a load balancer, each keeps its own counters — real limits become `(configured limit × worker count)`, and System Monitoring only reflects the worker that handled the request. A shared store (e.g. Redis via `RATELIMIT_STORAGE_URI`) fixes the first; the second would need a shared metrics backend, not implemented here.
- **No email provider configured out of the box**: `SMTPEmailService` (`MAIL_BACKEND=smtp`) exists and sends real branded email over any SMTP server, but the default in every template (including the production one) is still `MAIL_BACKEND=console`, which only logs emails — an operator has to explicitly set the `MAIL_*` env vars to a real provider before password reset/email verification links reach a real inbox.
- **Contact section uses a placeholder mailto address**: `contact@cybershield.example` is clearly labeled as a placeholder in the UI — there's no real inbox behind it yet.
- **No automated Lighthouse/axe accessibility audit was run**: the accessibility pass was a manual, targeted review (focus states, aria-labels, semantic structure, keyboard nav) rather than an automated scored audit — real gaps may remain that a dedicated tool would catch.
- **No load/stress testing**: performance work this phase was code-splitting and a build-output check, not a benchmark against concurrent traffic.

**Added in Phase 10 (Security Hardening), still out of scope:**

A phased security audit (SSRF protections, file-upload hardening, refresh-token revocation, account lockout, admin RBAC, dependency scanning, HSTS/CSP headers, audit logging, secrets hygiene) found most of the platform's security posture already sound — the gaps that existed were fixed additively (e.g. a timeout around email parsing, per-account login lockout, session revocation on password change, audit-logging the last few unlogged action points, frontend security headers). Three items were explicitly scoped as documentation-only, not implementation, for this phase:

- **Two-factor authentication (TOTP)**: not implemented. Login today is single-factor (password + the account-lockout/rate-limiting already in place). Adding optional TOTP 2FA would mean a new `User` secret field (encrypted at rest), a QR-code enrollment flow, backup/recovery codes, and a second verification step in the login route — a real feature addition with its own UX, not a hardening tweak, so it's deliberately left as future work rather than bolted on inside a security-review pass.
- **Automated database backups with a tested restore procedure**: not implemented. This is an operational/infrastructure concern (a scheduled `pg_dump`/managed-Postgres snapshot policy, off-site storage, and a periodically *tested* restore drill) that depends entirely on where and how you actually host Postgres in production — there's no code-level backup mechanism to add inside this repository, and a real backup story requires making hosting decisions (managed DB vs. self-hosted, retention window, restore SLA) that are yours to make, not something to assume from inside the codebase.
- **A WAF or Cloudflare (or equivalent) in front of production**: not implemented, and can't be — this is a hosting/infrastructure decision (which CDN/WAF provider, DNS delegation, rule tuning) made outside this repository, not a code change. The application-layer protections a WAF would complement (rate limiting, CSP/security headers, SSRF guards, input validation) are already in place; a WAF is an additional layer on top of those, not a replacement for them, and belongs at the hosting/deployment layer documented in the "Deployment (production)" section above.
