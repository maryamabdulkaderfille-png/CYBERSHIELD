def register_security_headers(app):
    """Phase 7 enterprise security review: CSP, HSTS, X-Frame-Options,
    X-Content-Type-Options, Referrer-Policy, and Permissions-Policy were all
    already in place (Phase 1). This adds Cross-Origin-Opener-Policy (COOP)
    and Cross-Origin-Resource-Policy (CORP) — with one deliberate choice:
    CORP is set to "cross-origin", not the stricter "same-origin", because
    this API is *intentionally* consumed cross-origin by both the separately
    hosted frontend (a different port) and the browser extension (a
    chrome-extension:// origin) — CORP: same-origin would silently break
    every response those two legitimate clients already read, which
    "preserve all APIs / preserve all extension functionality" rules out.
    Access is still controlled by CORS (see EXTENSION_ORIGINS/FRONTEND_ORIGIN
    in app/config.py) and auth, which is the correct gate for this
    architecture — CORP here only documents that cross-origin reads are
    deliberate, not an oversight. This also documents the rest of the
    review:

    - Cookies (JWT_COOKIE_SECURE/SAMESITE, httpOnly via flask-jwt-extended,
      CSRF double-submit): already correct (see app/config.py) — Phase 7
      changed nothing here, since there was nothing to fix.
    - CSP `default-src 'none'` is intentionally maximal: this is a pure JSON
      API serving no HTML/CSS/JS of its own, so there's no script-src/
      style-src to relax.
    """

    @app.after_request
    def _apply_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
        if not app.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
