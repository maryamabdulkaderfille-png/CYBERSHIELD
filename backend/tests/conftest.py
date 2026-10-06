import pytest

from app import create_app
from app.extensions import db as _db
from app.services.url_scanner.domain_age_provider import DomainAgeResult
from app.services.url_scanner.network import CertificateInfo, RedirectCheckResult, RedirectHop
from app.services.url_scanner.rules import domain_age, redirect_check, ssl_certificate


@pytest.fixture(autouse=True)
def stub_url_scanner_network_calls(monkeypatch):
    """Every test runs fully offline: SSL/redirect/WHOIS lookups in the URL
    scanner are real network calls in production, but tests stub them so the
    suite is deterministic and doesn't depend on outbound internet access."""
    monkeypatch.setattr(
        ssl_certificate, "get_certificate_info", lambda hostname, ips: CertificateInfo(status="valid")
    )
    monkeypatch.setattr(
        redirect_check,
        "safe_follow_redirects",
        lambda url, hostname: RedirectCheckResult(
            ok=True, hops=[RedirectHop(url=url, status_code=200)], final_url=url, cross_domain=False
        ),
    )

    class _EstablishedDomainAgeProvider:
        def lookup(self, domain):
            return DomainAgeResult(status="established", age_days=3000)

    monkeypatch.setattr(domain_age, "get_domain_age_provider", lambda: _EstablishedDomainAgeProvider())


@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def csrf_header(client, cookie_name="csrf_access_token"):
    """Read the double-submit CSRF cookie the way a real frontend would, for
    state-changing requests against JWT-protected endpoints."""
    cookie = client.get_cookie(cookie_name)
    return {"X-CSRF-TOKEN": cookie.value} if cookie else {}


@pytest.fixture()
def registered_user_id(app):
    """A real user row created directly via auth_service (not the HTTP
    endpoint) — for service-layer tests that need a user_id but don't care
    about the register/login HTTP flow itself."""
    from app.services import auth_service

    with app.app_context():
        user = auth_service.register_user("Jane Doe", "janedoe", "jane@example.com", "StrongPass1!")
        return user.id


@pytest.fixture()
def second_user_id(app):
    from app.services import auth_service

    with app.app_context():
        user = auth_service.register_user("Second User", "seconduser", "second@example.com", "StrongPass1!")
        return user.id


@pytest.fixture()
def registered_user(client):
    payload = {
        "full_name": "Jane Doe",
        "username": "janedoe",
        "email": "jane@example.com",
        "password": "StrongPass1!",
        "confirm_password": "StrongPass1!",
    }
    client.post("/api/v1/auth/register", json=payload)
    return payload


@pytest.fixture()
def admin_user(client, app):
    """There is deliberately no API-level way to create an admin account
    (see app/models/user.py's UserRole / register_user) — self-promotion to
    admin must never be possible over HTTP. Tests that need one register a
    normal account through the real endpoint and then promote it via a
    direct DB mutation, the same way a real operator would (e.g. a one-off
    `flask shell` command), not through any route.
    """
    payload = {
        "full_name": "Ada Admin",
        "username": "adaadmin",
        "email": "admin@example.com",
        "password": "StrongPass1!",
        "confirm_password": "StrongPass1!",
    }
    client.post("/api/v1/auth/register", json=payload)
    with app.app_context():
        from app.models.user import User, UserRole

        user = User.query.filter_by(email=payload["email"]).first()
        user.role = UserRole.ADMIN
        user.is_verified = True
        _db.session.commit()
    return payload
