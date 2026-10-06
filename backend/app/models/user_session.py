from app.extensions import db
from app.utils.time import utcnow


class UserSession(db.Model):
    """A lightweight audit trail of logins, recorded alongside the existing
    JWT issuance flow (see auth_service.issue_token_pair) — not a
    replacement for it. Revoking a session reuses the existing
    TokenBlocklist mechanism (auth_service.revoke_token) rather than
    introducing a second revocation path.
    """

    __tablename__ = "user_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    refresh_jti = db.Column(db.String(36), nullable=False, unique=True, index=True)
    # Shared by the access+refresh token issued together at login (see
    # auth_service.issue_token_pair) — lets routes authenticated by the
    # *access* token identify "this session" without needing the refresh
    # cookie, which is only ever sent to /auth/refresh.
    session_key = db.Column(db.String(64), nullable=False, unique=True, index=True)
    user_agent = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime(), nullable=False, default=utcnow)
    last_seen_at = db.Column(db.DateTime(), nullable=False, default=utcnow)
    revoked_at = db.Column(db.DateTime(), nullable=True)
    expires_at = db.Column(db.DateTime(), nullable=False)

    def to_dict(self, *, current_session_key: str | None = None) -> dict:
        return {
            "id": self.id,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "created_at": f"{self.created_at.isoformat()}Z",
            "last_seen_at": f"{self.last_seen_at.isoformat()}Z",
            "is_revoked": self.revoked_at is not None,
            "is_current": current_session_key is not None and self.session_key == current_session_key,
        }
