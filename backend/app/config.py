import os
from datetime import timedelta


def _bool_env(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _list_env(name: str) -> list[str]:
    """Comma-separated env var -> a clean list of non-empty, trimmed values."""
    return [item.strip() for item in os.environ.get(name, "").split(",") if item.strip()]


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "")
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_ACCESS_COOKIE_NAME = "access_token"
    JWT_REFRESH_COOKIE_NAME = "refresh_token"
    JWT_ACCESS_COOKIE_PATH = "/api/v1/"
    JWT_REFRESH_COOKIE_PATH = "/api/v1/auth/refresh"
    JWT_COOKIE_SECURE = _bool_env("JWT_COOKIE_SECURE", True)
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")
    FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", FRONTEND_ORIGIN)

    # Phase 6: the browser extension calls this same API from a
    # chrome-extension://<id> / moz-extension://<id> origin using the same
    # cookie-based auth as the web app. Each installed extension gets a
    # different id, so — unlike FRONTEND_ORIGIN — this is a whitelist you
    # populate once you know your extension's id(s), not a fixed default.
    # Deliberately not a wildcard: allowing any chrome-extension:// origin
    # would let *any* other installed extension ride the user's session
    # cookie against this API.
    EXTENSION_ORIGINS = _list_env("EXTENSION_ORIGINS")

    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

    # Off by default: only enable behind a reverse proxy/load balancer you
    # control, so it can't be used to spoof the client IP that rate limiting
    # and audit logging key off of (see app.__init__._apply_proxy_fix).
    TRUST_PROXY_HEADERS = _bool_env("TRUST_PROXY_HEADERS", False)

    PASSWORD_RESET_TOKEN_TTL_MINUTES = int(os.environ.get("PASSWORD_RESET_TOKEN_TTL_MINUTES", "30"))
    EMAIL_VERIFICATION_TOKEN_TTL_HOURS = int(os.environ.get("EMAIL_VERIFICATION_TOKEN_TTL_HOURS", "24"))

    # Threat Intelligence integrations
    VIRUSTOTAL_API_KEY = os.environ.get("VIRUSTOTAL_API_KEY", "")
    # URLhaus (abuse.ch) now requires an Auth-Key header on every request —
    # without this, external_threat_intel's URLhaus check reports itself as
    # "unavailable" (never a false "clean") rather than silently skipping.
    URLHAUS_AUTH_KEY = os.environ.get("URLHAUS_AUTH_KEY", "")

    # "Sign in with Google" — additive alternative to email/password (Phase 11).
    # Empty by default: the /auth/google/* routes are only registered with a
    # real provider once both of these are set (see app/__init__.py), so a
    # deployment that never configures Google Sign-In is completely unaffected.
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

    MAIL_BACKEND = os.environ.get("MAIL_BACKEND", "console")
    MAIL_FROM = os.environ.get("MAIL_FROM", "CyberShield <no-reply@cybershield.local>")
    # Only read/used when MAIL_BACKEND=smtp (see app/services/email_service.py's
    # SMTPEmailService). Left empty by default so the console backend keeps
    # working with zero configuration in dev/CI.
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_USE_TLS = _bool_env("MAIL_USE_TLS", True)

    # Resend-verification abuse guard (Section 7 of the email verification
    # spec) — a per-account/hour cap layered on top of the existing per-IP
    # Flask-Limiter rate limit on the route itself, since an attacker can
    # spread requests across IPs but not across accounts.
    VERIFICATION_RESEND_MAX_PER_HOUR = int(os.environ.get("VERIFICATION_RESEND_MAX_PER_HOUR", "3"))

    # Hard WSGI-level cap on request body size (Werkzeug rejects with 413
    # before the body is buffered into memory) — the email-upload endpoint
    # has its own tighter, user-facing size check, but this is the backstop
    # that actually prevents an oversized request from being read into
    # memory in the first place, regardless of which endpoint receives it.
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_BYTES", 8 * 1024 * 1024))

    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True
    JWT_COOKIE_SECURE = _bool_env("JWT_COOKIE_SECURE", False)


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "testing-secret-key")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "testing-jwt-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
    JWT_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False
    MAIL_BACKEND = "console"


class ProductionConfig(Config):
    JWT_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None):
    name = name or os.environ.get("FLASK_ENV", "development")
    return config_by_name.get(name, DevelopmentConfig)
