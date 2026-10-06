import hashlib
import secrets
from datetime import timedelta

from flask import current_app

from app.extensions import db
from app.models.user_token import TokenPurpose, UserToken
from app.utils.time import utcnow


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _ttl_for(purpose: str) -> timedelta:
    if purpose == TokenPurpose.PASSWORD_RESET:
        return timedelta(minutes=current_app.config["PASSWORD_RESET_TOKEN_TTL_MINUTES"])
    return timedelta(hours=current_app.config["EMAIL_VERIFICATION_TOKEN_TTL_HOURS"])


def issue_token(user_id: str, purpose: str) -> str:
    """Create a one-time token, persist only its hash, and return the raw value."""
    UserToken.query.filter_by(user_id=user_id, purpose=purpose, used_at=None).delete()

    raw_token = secrets.token_urlsafe(32)
    record = UserToken(
        user_id=user_id,
        token_hash=_hash_token(raw_token),
        purpose=purpose,
        expires_at=utcnow() + _ttl_for(purpose),
    )
    db.session.add(record)
    db.session.commit()
    return raw_token


def consume_token(raw_token: str, purpose: str) -> UserToken | None:
    """Look up a token by hash, validate it, and mark it used. Returns None if invalid/expired."""
    record = UserToken.query.filter_by(token_hash=_hash_token(raw_token), purpose=purpose).first()
    if record is None or not record.is_valid():
        return None
    record.used_at = utcnow()
    db.session.commit()
    return record
