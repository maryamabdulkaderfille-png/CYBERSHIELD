from datetime import timedelta
from email import message_from_string
from unittest.mock import MagicMock, patch

from app.extensions import db
from app.models.user import User
from app.models.user_token import TokenPurpose, UserToken
from app.services import auth_service, token_service
from app.utils.time import utcnow


def _sent_verification_links(monkeypatch):
    """Patches the email service so tests can assert on what would have been
    sent without touching the network or the console logger."""
    calls = []
    monkeypatch.setattr(
        "app.services.auth_service.get_email_service",
        lambda: MagicMock(send_verification_email=lambda to, name, token: calls.append((to, name, token))),
    )
    return calls


# --- Registration ----------------------------------------------------------


def test_new_user_starts_unverified(app, registered_user_id):
    with app.app_context():
        user = db.session.get(User, registered_user_id)
        assert user.is_verified is False


def test_registration_sends_verification_email(app, monkeypatch):
    calls = _sent_verification_links(monkeypatch)
    with app.app_context():
        auth_service.register_user("Jane Doe", "janedoe", "jane@example.com", "StrongPass1!")
    assert len(calls) == 1
    to_email, name, raw_token = calls[0]
    assert to_email == "jane@example.com"
    assert name == "Jane Doe"
    assert len(raw_token) > 20  # secrets.token_urlsafe(32), not guessable


def test_verification_token_is_stored_only_as_a_hash(app, registered_user_id):
    with app.app_context():
        raw_token = token_service.issue_token(registered_user_id, TokenPurpose.EMAIL_VERIFICATION)
        record = UserToken.query.filter_by(user_id=registered_user_id, purpose=TokenPurpose.EMAIL_VERIFICATION).first()
        assert record.token_hash != raw_token
        assert len(record.token_hash) == 64  # sha256 hex digest


# --- Verification endpoint --------------------------------------------------


def test_valid_token_verifies_the_account(app, client, registered_user_id):
    with app.app_context():
        raw_token = token_service.issue_token(registered_user_id, TokenPurpose.EMAIL_VERIFICATION)

    response = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert response.status_code == 200
    body = response.get_json()
    assert body["user"]["is_verified"] is True
    # The raw/hashed token must never be echoed back.
    assert "token" not in body and "token_hash" not in str(body)


def test_invalid_token_is_rejected(client):
    response = client.post("/api/v1/auth/verify-email", json={"token": "not-a-real-token"})
    assert response.status_code == 400


def test_expired_token_is_rejected(app, client, registered_user_id):
    with app.app_context():
        raw_token = token_service.issue_token(registered_user_id, TokenPurpose.EMAIL_VERIFICATION)
        record = UserToken.query.filter_by(
            user_id=registered_user_id, purpose=TokenPurpose.EMAIL_VERIFICATION
        ).first()
        record.expires_at = utcnow() - timedelta(hours=1)

        db.session.commit()

    response = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert response.status_code == 400
    with app.app_context():
        assert db.session.get(User, registered_user_id).is_verified is False


def test_used_token_cannot_be_reused(app, client, registered_user_id):
    with app.app_context():
        raw_token = token_service.issue_token(registered_user_id, TokenPurpose.EMAIL_VERIFICATION)

    first = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert first.status_code == 200

    second = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert second.status_code == 400


def test_reissuing_a_token_invalidates_the_previous_one(app, registered_user_id):
    with app.app_context():
        first_token = token_service.issue_token(registered_user_id, TokenPurpose.EMAIL_VERIFICATION)
        token_service.issue_token(registered_user_id, TokenPurpose.EMAIL_VERIFICATION)

        assert token_service.consume_token(first_token, TokenPurpose.EMAIL_VERIFICATION) is None


# --- Resend verification ----------------------------------------------------


def test_resend_verification_issues_a_fresh_token(app, monkeypatch, registered_user_id):
    calls = _sent_verification_links(monkeypatch)
    with app.app_context():
        user = db.session.get(User, registered_user_id)
        auth_service.resend_verification_email(user.email)
    assert len(calls) == 1


def test_resend_verification_is_a_noop_for_already_verified_account(app, monkeypatch, registered_user_id):
    calls = _sent_verification_links(monkeypatch)
    with app.app_context():
        user = db.session.get(User, registered_user_id)
        user.is_verified = True

        db.session.commit()
        auth_service.resend_verification_email(user.email)
    assert calls == []


def test_resend_verification_does_not_leak_account_existence(app, monkeypatch):
    calls = _sent_verification_links(monkeypatch)
    with app.app_context():
        auth_service.resend_verification_email("nobody-registered@example.com")
    assert calls == []  # silently ignored, same as a real-but-verified account


def test_resend_verification_route_returns_generic_message_regardless(client):
    known = client.post("/api/v1/auth/resend-verification", json={"email": "nobody@example.com"})
    assert known.status_code == 200
    assert "email has been sent" in known.get_json()["message"]


def test_resend_verification_rate_limited_per_account(app, monkeypatch, registered_user_id):
    """Section 7: max VERIFICATION_RESEND_MAX_PER_HOUR (default 3) emails per
    account per rolling hour, enforced independent of the per-IP route limiter
    (which is disabled under TestingConfig)."""
    calls = _sent_verification_links(monkeypatch)
    with app.app_context():
        user = db.session.get(User, registered_user_id)
        for _ in range(5):
            auth_service.resend_verification_email(user.email)
    assert len(calls) == 3


def test_resend_verification_over_http_stays_200_after_cap(app, client, registered_user):
    """The rate-limit cap must not change the HTTP response shape/status —
    otherwise it becomes an account-enumeration oracle."""
    for _ in range(5):
        response = client.post("/api/v1/auth/resend-verification", json={"email": registered_user["email"]})
        assert response.status_code == 200
        assert "email has been sent" in response.get_json()["message"]


# --- Login behavior for unverified users ------------------------------------


def test_unverified_user_can_still_log_in(client, registered_user):
    """Unverified users are allowed to log in (Section 8) — verification is
    surfaced as a banner/resend prompt in the frontend, not a login block."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    assert response.status_code == 200
    assert response.get_json()["user"]["is_verified"] is False


def test_verified_user_login_unaffected(app, client, registered_user):
    with app.app_context():
        user = User.query.filter_by(email=registered_user["email"]).first()
        user.is_verified = True

        db.session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    assert response.status_code == 200
    assert response.get_json()["user"]["is_verified"] is True


# --- SMTP backend ------------------------------------------------------------


def test_smtp_backend_sends_via_configured_server(app):
    from app.services.email_service import SMTPEmailService

    app.config.update(
        MAIL_SERVER="smtp.example.com",
        MAIL_PORT=587,
        MAIL_USERNAME="apikey",
        MAIL_PASSWORD="secret",
        MAIL_USE_TLS=True,
        MAIL_FROM="CyberShield <no-reply@cybershield.local>",
        FRONTEND_BASE_URL="https://app.example.com",
    )
    with app.app_context(), patch("smtplib.SMTP") as smtp_cls:
        smtp_instance = smtp_cls.return_value.__enter__.return_value
        SMTPEmailService().send_verification_email("jane@example.com", "Jane Doe", "raw-token-value")

        smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=10)
        smtp_instance.starttls.assert_called_once()
        smtp_instance.login.assert_called_once_with("apikey", "secret")
        assert smtp_instance.sendmail.call_count == 1
        from_addr, to_addrs, message_string = smtp_instance.sendmail.call_args[0]
        assert to_addrs == ["jane@example.com"]
        assert "Verify your CyberShield account" in message_string
        assert "https://app.example.com/verify-email?token=raw-token-value" in message_string


def test_smtp_backend_escapes_html_special_characters_in_name(app):
    """A full_name containing HTML/script-like content must never be
    interpreted as markup in the HTML part of the email."""
    from app.services.email_service import SMTPEmailService

    app.config.update(
        MAIL_SERVER="smtp.example.com", MAIL_PORT=587, MAIL_USERNAME="", MAIL_PASSWORD="",
        MAIL_USE_TLS=False, MAIL_FROM="CyberShield <no-reply@cybershield.local>",
        FRONTEND_BASE_URL="https://app.example.com",
    )
    with app.app_context(), patch("smtplib.SMTP") as smtp_cls:
        smtp_instance = smtp_cls.return_value.__enter__.return_value
        SMTPEmailService().send_verification_email(
            "jane@example.com", "<script>alert(1)</script>", "raw-token-value"
        )
        message_string = smtp_instance.sendmail.call_args[0][2]

        parsed = message_from_string(message_string)
        html_part = next(part for part in parsed.walk() if part.get_content_type() == "text/html")
        html_body = html_part.get_payload(decode=True).decode(html_part.get_content_charset() or "utf-8")

        assert "<script>alert(1)</script>" not in html_body
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html_body
