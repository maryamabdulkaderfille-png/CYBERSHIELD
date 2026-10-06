import re
import secrets
from datetime import datetime, timedelta

from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token

from app.extensions import bcrypt, db
from app.models.audit_log import AuditAction
from app.models.token import TokenBlocklist
from app.models.user import User
from app.models.user_token import TokenPurpose
from app.services import audit_service, token_service
from app.services.email_service import get_email_service
from app.utils.errors import APIError
from app.utils.time import utcnow

# Account lockout (Phase 10) — an account-keyed layer on top of the existing
# IP-keyed rate limit on /auth/login (see extensions.py's limiter), not a
# replacement for it.
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


def register_user(full_name: str, username: str, email: str, password: str) -> User:
    email = email.lower().strip()
    username = username.strip()

    if User.query.filter_by(email=email).first() is not None:
        raise APIError("An account with this email already exists.", 409)
    if User.query.filter_by(username=username).first() is not None:
        raise APIError("This username is already taken.", 409)

    user = User(
        full_name=full_name.strip(),
        username=username,
        email=email,
        password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
    )
    db.session.add(user)
    db.session.commit()

    raw_token = token_service.issue_token(user.id, TokenPurpose.EMAIL_VERIFICATION)
    get_email_service().send_verification_email(user.email, user.full_name, raw_token)

    return user


def _generate_unique_username(email: str) -> str:
    """Derives a username from an email's local-part for a Google sign-up,
    where no username is ever supplied — sanitized to the same USERNAME_RE
    rules /auth/register already enforces, then de-duplicated with a
    numeric suffix so it never collides with an existing row."""
    base = re.sub(r"[^a-zA-Z0-9_]", "", email.split("@", 1)[0])[:28] or "user"
    if len(base) < 3:
        base = base.ljust(3, "0")

    candidate = base
    suffix = 1
    while User.query.filter_by(username=candidate).first() is not None:
        candidate = f"{base}{suffix}"[:32]
        suffix += 1
    return candidate


def find_or_create_google_user(google_id: str, email: str, full_name: str) -> User:
    """Account linking (Phase 11): a Google identity always resolves to
    exactly one CyberShield account, in this priority order:
    1. An account already linked to this exact google_id -> that account.
    2. An existing password account with the same email -> link google_id
       onto it (Google has already verified the email, so this is safe);
       its password_hash and existing login are left completely untouched
       — the user can keep using either sign-in method going forward.
    3. Neither exists -> a brand-new, password-less account.
    """
    email = email.lower().strip()

    user = User.query.filter_by(google_id=google_id).first()
    if user is not None:
        return user

    user = User.query.filter_by(email=email).first()
    if user is not None:
        user.google_id = google_id
        db.session.commit()
        return user

    user = User(
        full_name=full_name.strip() or email.split("@", 1)[0],
        username=_generate_unique_username(email),
        email=email,
        password_hash=None,
        google_id=google_id,
        is_verified=True,  # Google has already verified this email address.
    )
    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(email: str, password: str) -> User:
    user = User.query.filter_by(email=email.lower().strip()).first()

    # Checked before the password so a locked account doesn't leak whether
    # the submitted password would otherwise have been correct.
    if user is not None and user.locked_until is not None and user.locked_until > utcnow():
        raise APIError(
            "This account is temporarily locked due to repeated failed login attempts. "
            "Please try again later.",
            403,
        )

    # A Google-only account (Phase 11) has no password_hash to check against
    # — treated the same as "wrong password" below, not a crash, and not a
    # different-looking error that would reveal the account's sign-in method.
    if user is None or user.password_hash is None or not bcrypt.check_password_hash(user.password_hash, password):
        if user is not None:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
                user.locked_until = utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            db.session.commit()
        raise APIError("Invalid email or password.", 401)
    if not user.is_active:
        raise APIError("This account has been deactivated.", 403)

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = utcnow()
    db.session.commit()
    return user


def issue_token_pair(user: User) -> tuple[str, str, str]:
    """`sid` is a stable per-login identifier shared by both tokens in the
    pair — distinct from either token's own `jti`. The refresh cookie is
    scoped to /auth/refresh only (JWT_REFRESH_COOKIE_PATH), so it's never
    present on other requests; `sid` lets session_service recognize "this
    login" from the *access* token instead, which every request carries.
    """
    session_key = secrets.token_urlsafe(16)
    additional_claims = {"role": user.role, "sid": session_key}
    access_token = create_access_token(identity=user.id, additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=user.id, additional_claims=additional_claims)
    return access_token, refresh_token, session_key


def revoke_token(jti: str, token_type: str, user_id: str, expires_at: datetime) -> None:
    db.session.add(
        TokenBlocklist(jti=jti, token_type=token_type, user_id=user_id, expires_at=expires_at)
    )
    db.session.commit()


def is_token_revoked(jti: str) -> bool:
    return TokenBlocklist.query.filter_by(jti=jti).first() is not None


def request_password_reset(email: str) -> None:
    user = User.query.filter_by(email=email.lower().strip()).first()
    if user is None:
        return  # Don't reveal whether an account exists.
    raw_token = token_service.issue_token(user.id, TokenPurpose.PASSWORD_RESET)
    get_email_service().send_password_reset_email(user.email, user.full_name, raw_token)


def reset_password(raw_token: str, new_password: str) -> User:
    record = token_service.consume_token(raw_token, TokenPurpose.PASSWORD_RESET)
    if record is None:
        raise APIError("This password reset link is invalid or has expired.", 400)

    user = db.session.get(User, record.user_id)
    if user is None:
        raise APIError("This password reset link is invalid or has expired.", 400)

    user.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
    db.session.commit()
    return user


def verify_email(raw_token: str) -> User:
    record = token_service.consume_token(raw_token, TokenPurpose.EMAIL_VERIFICATION)
    if record is None:
        raise APIError("This verification link is invalid or has expired.", 400)

    user = db.session.get(User, record.user_id)
    if user is None:
        raise APIError("This verification link is invalid or has expired.", 400)

    user.is_verified = True
    db.session.commit()
    return user


def resend_verification_email(email: str) -> None:
    user = User.query.filter_by(email=email.lower().strip()).first()
    if user is None or user.is_verified:
        return  # Don't reveal account existence/verification state.

    # Per-account/hour cap (Section 7): fails silently rather than returning
    # a distinct error, so a caller spamming this endpoint for one address
    # can't use the response to infer that the account exists and is
    # unverified — the route's response is identical either way. Counted via
    # the append-only audit log rather than the user_tokens table, since
    # issue_token deletes the previous *unused* token on every reissue —
    # counting rows there would undercount how many were actually sent.
    since = utcnow() - timedelta(hours=1)
    recent_sends = audit_service.count_actions(user.id, AuditAction.EMAIL_VERIFICATION_SENT, since)
    if recent_sends >= current_app.config["VERIFICATION_RESEND_MAX_PER_HOUR"]:
        return

    raw_token = token_service.issue_token(user.id, TokenPurpose.EMAIL_VERIFICATION)
    get_email_service().send_verification_email(user.email, user.full_name, raw_token)
    audit_service.log_action(user.id, AuditAction.EMAIL_VERIFICATION_SENT)


def change_password(user: User, current_password: str, new_password: str) -> None:
    if user.password_hash is None:
        raise APIError("This account doesn't have a password set — it was created via Google Sign-In.", 400)
    if not bcrypt.check_password_hash(user.password_hash, current_password):
        raise APIError("Current password is incorrect.", 401)
    user.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
    db.session.commit()


def deactivate_account(user: User, password: str) -> None:
    """Reuses the existing `is_active` flag (already enforced by
    `authenticate_user` and the `/auth/refresh` route) rather than adding a
    separate soft-delete mechanism. The route layer additionally revokes the
    caller's current tokens and all other sessions, the same way `/auth/logout`
    already does, so the deactivation takes effect immediately rather than
    waiting for the access token to expire."""
    if user.password_hash is None:
        raise APIError("This account doesn't have a password set — it was created via Google Sign-In.", 400)
    if not bcrypt.check_password_hash(user.password_hash, password):
        raise APIError("Password is incorrect.", 401)
    user.is_active = False
    db.session.commit()


def update_profile(user: User, full_name: str | None, username: str | None) -> User:
    if username and username != user.username:
        if User.query.filter_by(username=username).first() is not None:
            raise APIError("This username is already taken.", 409)
        user.username = username
    if full_name:
        user.full_name = full_name
    db.session.commit()
    return user
