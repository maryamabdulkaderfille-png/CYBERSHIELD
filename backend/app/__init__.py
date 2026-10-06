import logging

from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from app.cli import register_cli
from app.config import get_config
from app.extensions import bcrypt, cors, db, jwt, limiter, migrate, oauth
from app.middleware.request_metrics import register_request_metrics
from app.middleware.security_headers import register_security_headers
from app.scheduler import init_scheduler
from app.utils.errors import register_error_handlers


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    if not app.config.get("TESTING") and not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY must be set via environment variable.")
    if not app.config.get("TESTING") and not app.config["JWT_SECRET_KEY"]:
        raise RuntimeError("JWT_SECRET_KEY must be set via environment variable.")

    _apply_proxy_fix(app)
    _init_extensions(app)
    _register_jwt_callbacks()
    _register_blueprints(app)
    register_error_handlers(app)
    register_security_headers(app)
    register_request_metrics(app)
    register_cli(app)
    init_scheduler(app)

    if not app.debug and not app.testing:
        logging.basicConfig(level=logging.INFO)

    @app.get("/health")
    def health():
        # Deliberately unauthenticated and dependency-light — this is what
        # Docker/Compose/an orchestrator's healthcheck actually calls, so it
        # must work without a session and never itself throw. Reuses the same
        # DB check the admin System Monitoring page already shows (Phase 7)
        # rather than duplicating a second "is the database up" query.
        from app.services.system_monitoring_service import get_database_status

        database = get_database_status()
        is_healthy = database["status"] == "healthy"
        return jsonify({"status": "ok" if is_healthy else "degraded", "service": "cybershield-backend", "database": database}), (
            200 if is_healthy else 503
        )

    return app


def _apply_proxy_fix(app: Flask) -> None:
    """Trust one hop of X-Forwarded-For/-Proto so request.remote_addr (used by
    rate limiting) reflects the real client instead of the proxy, when
    actually deployed behind one. Off by default — enabling this without a
    proxy in front would let clients spoof their own rate-limit identity via
    the X-Forwarded-For header."""
    if app.config.get("TRUST_PROXY_HEADERS"):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    allowed_origins = [app.config["FRONTEND_ORIGIN"], *app.config["EXTENSION_ORIGINS"]]
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": allowed_origins}},
        supports_credentials=True,
    )
    _init_google_oauth(app)


def _init_google_oauth(app: Flask) -> None:
    """Only registers a real Google provider once both credentials are
    actually configured — an unconfigured deployment (the default) leaves
    /auth/google/* routes returning a clean error rather than the app
    failing to start, so existing email/password-only deployments are
    completely unaffected."""
    oauth.init_app(app)
    if app.config["GOOGLE_CLIENT_ID"] and app.config["GOOGLE_CLIENT_SECRET"]:
        oauth.register(
            name="google",
            client_id=app.config["GOOGLE_CLIENT_ID"],
            client_secret=app.config["GOOGLE_CLIENT_SECRET"],
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )


def _register_blueprints(app: Flask) -> None:
    from app.routes.v1 import api_v1_bp

    app.register_blueprint(api_v1_bp)


def _register_jwt_callbacks() -> None:
    from app.models.user import User
    from app.services.auth_service import is_token_revoked

    @jwt.user_lookup_loader
    def _user_lookup(_jwt_header, jwt_data):
        return db.session.get(User, jwt_data["sub"])

    @jwt.token_in_blocklist_loader
    def _check_if_revoked(_jwt_header, jwt_data):
        return is_token_revoked(jwt_data["jti"])

    @jwt.expired_token_loader
    def _expired_token(_jwt_header, _jwt_data):
        return jsonify({"error": "Token has expired."}), 401

    @jwt.invalid_token_loader
    def _invalid_token(_reason):
        return jsonify({"error": "Invalid authentication token."}), 401

    @jwt.unauthorized_loader
    def _missing_token(_reason):
        return jsonify({"error": "Authentication required."}), 401

    @jwt.revoked_token_loader
    def _revoked_token(_jwt_header, _jwt_data):
        return jsonify({"error": "Token has been revoked."}), 401
