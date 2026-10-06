"""Login session tracking — an audit trail layered on top of the existing
JWT issuance flow, not a replacement for it. Actual revocation reuses
auth_service.revoke_token (the same TokenBlocklist mechanism `/auth/logout`
already uses) so there is exactly one way a refresh token gets revoked.
"""

from datetime import datetime, timedelta, timezone

from flask_jwt_extended import decode_token

from app.extensions import db
from app.models.user_session import UserSession
from app.services import auth_service
from app.utils.time import utcnow

# "Active" = a non-revoked, non-expired session touched within this window.
# Matches the 15-minute access-token TTL: last_seen_at is only updated on a
# token refresh (see touch_session, called from /auth/refresh), and the
# frontend only refreshes reactively when the access token has just expired
# — there's no periodic heartbeat — so a genuinely active user's last_seen_at
# can lag up to one access-token lifetime behind their real last action.
ACTIVE_SESSION_WINDOW_MINUTES = 15


def record_session(
    user_id: str, refresh_token: str, session_key: str, user_agent: str | None, ip_address: str | None
) -> UserSession:
    claims = decode_token(refresh_token)
    session = UserSession(
        user_id=user_id,
        refresh_jti=claims["jti"],
        session_key=session_key,
        user_agent=(user_agent or "")[:255] or None,
        ip_address=ip_address,
        expires_at=datetime.fromtimestamp(claims["exp"], tz=timezone.utc).replace(tzinfo=None),
    )
    db.session.add(session)
    db.session.commit()
    return session


def mark_session_revoked_by_jti(refresh_jti: str) -> None:
    """Called from /auth/logout, which already revokes the refresh token
    itself via TokenBlocklist — this just keeps the session list's
    is_revoked flag in sync with that."""
    session = UserSession.query.filter_by(refresh_jti=refresh_jti).first()
    if session is not None and session.revoked_at is None:
        session.revoked_at = utcnow()
        db.session.commit()


def touch_session(refresh_jti: str) -> None:
    """Called on token refresh to keep last_seen_at current."""
    session = UserSession.query.filter_by(refresh_jti=refresh_jti).first()
    if session is not None:
        session.last_seen_at = utcnow()
        db.session.commit()


def list_sessions(user_id: str) -> list[UserSession]:
    return (
        UserSession.query.filter_by(user_id=user_id)
        .filter(UserSession.revoked_at.is_(None))
        .order_by(UserSession.last_seen_at.desc())
        .all()
    )


def revoke_session(user_id: str, session_id: int) -> bool:
    session = UserSession.query.filter_by(id=session_id, user_id=user_id).first()
    if session is None or session.revoked_at is not None:
        return False

    from app.utils.time import utcnow

    auth_service.revoke_token(
        jti=session.refresh_jti, token_type="refresh", user_id=user_id, expires_at=session.expires_at
    )
    session.revoked_at = utcnow()
    db.session.commit()
    return True


def count_active_users(window_minutes: int = ACTIVE_SESSION_WINDOW_MINUTES) -> int:
    """Distinct users with at least one live session touched within the
    window — reuses the existing UserSession audit trail rather than adding
    a second presence-tracking mechanism."""
    threshold = utcnow() - timedelta(minutes=window_minutes)
    return (
        db.session.query(UserSession.user_id)
        .filter(
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > utcnow(),
            UserSession.last_seen_at >= threshold,
        )
        .distinct()
        .count()
    )


def revoke_all_other_sessions(user_id: str, current_session_key: str | None) -> int:
    sessions = (
        UserSession.query.filter_by(user_id=user_id)
        .filter(UserSession.revoked_at.is_(None))
        .filter(UserSession.session_key != (current_session_key or ""))
        .all()
    )
    for session in sessions:
        revoke_session(user_id, session.id)
    return len(sessions)
