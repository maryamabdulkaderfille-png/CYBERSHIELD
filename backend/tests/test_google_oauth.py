from unittest.mock import MagicMock

from app.extensions import db, oauth
from app.models.user import User


# --- auth_service.find_or_create_google_user (unit-level, no HTTP) --------


def test_find_or_create_google_user_creates_new_account(app):
    from app.services import auth_service

    with app.app_context():
        user = auth_service.find_or_create_google_user(
            google_id="google-sub-1", email="newperson@example.com", full_name="New Person"
        )
        assert user.google_id == "google-sub-1"
        assert user.email == "newperson@example.com"
        assert user.password_hash is None
        assert user.is_verified is True
        assert user.username  # auto-generated, non-empty


def test_find_or_create_google_user_links_existing_password_account(app, registered_user_id):
    """The core requirement: signing in with Google using an email that
    already has a password account links google_id onto that SAME row —
    it must not create a duplicate user, and the password must survive."""
    from app.services import auth_service

    with app.app_context():
        existing = db.session.get(User, registered_user_id)
        assert existing.google_id is None
        original_password_hash = existing.password_hash

        linked = auth_service.find_or_create_google_user(
            google_id="google-sub-2", email=existing.email, full_name=existing.full_name
        )

        assert linked.id == existing.id  # same row, not a new user
        assert linked.google_id == "google-sub-2"
        assert linked.password_hash == original_password_hash  # untouched
        assert User.query.filter_by(email=existing.email).count() == 1  # no duplicate


def test_find_or_create_google_user_returns_same_account_on_repeat_login(app):
    from app.services import auth_service

    with app.app_context():
        first = auth_service.find_or_create_google_user(
            google_id="google-sub-3", email="repeat@example.com", full_name="Repeat User"
        )
        second = auth_service.find_or_create_google_user(
            google_id="google-sub-3", email="repeat@example.com", full_name="Repeat User"
        )
        assert first.id == second.id
        assert User.query.filter_by(google_id="google-sub-3").count() == 1


def test_linked_user_can_still_log_in_with_password(app, client, registered_user):
    """After linking, the existing password login must keep working exactly
    as before — Google Sign-In is additive, never a replacement."""
    from app.services import auth_service

    with app.app_context():
        auth_service.find_or_create_google_user(
            google_id="google-sub-4", email=registered_user["email"], full_name="Jane Doe"
        )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    assert response.status_code == 200
    assert "access_token" in response.headers.get("Set-Cookie", "")


def test_change_password_rejects_google_only_account(app):
    from app.services import auth_service
    from app.utils.errors import APIError

    with app.app_context():
        user = auth_service.find_or_create_google_user(
            google_id="google-sub-5", email="googleonly@example.com", full_name="Google Only"
        )
        try:
            auth_service.change_password(user, "anything", "NewPass1!")
            assert False, "expected an APIError"
        except APIError as err:
            assert err.status_code == 400


# --- Routes (mocking Authlib so tests stay fully offline) -----------------


def test_google_login_returns_501_when_unconfigured(client):
    """Default testing config has no GOOGLE_CLIENT_ID/SECRET set — the route
    must fail cleanly, not with an AttributeError."""
    response = client.get("/api/v1/auth/google/login")
    assert response.status_code == 501


def test_google_callback_returns_501_when_unconfigured(client):
    response = client.get("/api/v1/auth/google/callback")
    assert response.status_code == 501


def test_google_login_redirects_to_google_when_configured(client, monkeypatch):
    """Regression test: google_login() builds a redirect_uri via url_for()
    for the callback route. auth_bp is nested inside api_v1_bp, so that
    call must use the endpoint's full dotted name ("api_v1.auth.google_
    callback") — using just "auth.google_callback" raises a BuildError
    that this test would have caught before it ever reached a live
    server."""
    fake_google = MagicMock()
    fake_google.authorize_redirect.side_effect = lambda redirect_uri: __import__("flask").redirect(
        f"https://accounts.google.com/o/oauth2/v2/auth?redirect_uri={redirect_uri}"
    )
    monkeypatch.setattr(oauth, "google", fake_google, raising=False)

    response = client.get("/api/v1/auth/google/login")

    assert response.status_code == 302
    assert response.headers["Location"].startswith("https://accounts.google.com/")
    fake_google.authorize_redirect.assert_called_once()
    called_redirect_uri = fake_google.authorize_redirect.call_args[0][0]
    assert called_redirect_uri.endswith("/api/v1/auth/google/callback")


def test_google_callback_creates_user_and_sets_cookies(app, client, monkeypatch):
    fake_google = MagicMock()
    fake_google.authorize_access_token.return_value = {
        "userinfo": {
            "sub": "google-sub-new",
            "email": "fromgoogle@example.com",
            "email_verified": True,
            "name": "From Google",
        }
    }
    monkeypatch.setattr(oauth, "google", fake_google, raising=False)

    response = client.get("/api/v1/auth/google/callback?code=fake&state=fake")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    assert "access_token" in response.headers.get("Set-Cookie", "")

    with app.app_context():
        user = User.query.filter_by(email="fromgoogle@example.com").first()
        assert user is not None
        assert user.google_id == "google-sub-new"


def test_google_callback_redirects_to_login_on_unverified_email(client, monkeypatch):
    fake_google = MagicMock()
    fake_google.authorize_access_token.return_value = {
        "userinfo": {
            "sub": "google-sub-unverified",
            "email": "unverified@example.com",
            "email_verified": False,
            "name": "Unverified",
        }
    }
    monkeypatch.setattr(oauth, "google", fake_google, raising=False)

    response = client.get("/api/v1/auth/google/callback?code=fake&state=fake")

    assert response.status_code == 302
    assert "error=google_unverified_email" in response.headers["Location"]


def test_google_callback_redirects_to_login_on_authlib_failure(client, monkeypatch):
    fake_google = MagicMock()
    fake_google.authorize_access_token.side_effect = Exception("oauth error")
    monkeypatch.setattr(oauth, "google", fake_google, raising=False)

    response = client.get("/api/v1/auth/google/callback?code=fake&state=fake")

    assert response.status_code == 302
    assert "error=google_failed" in response.headers["Location"]
