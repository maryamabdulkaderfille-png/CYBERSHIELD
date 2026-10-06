from app.extensions import db
from app.utils.time import utcnow


class TokenPurpose:
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    ALL = (EMAIL_VERIFICATION, PASSWORD_RESET)


class UserToken(db.Model):
    """One-time tokens for email verification / password reset.

    Only the SHA-256 hash of the token is stored; the raw token is emailed to
    the user once and never persisted, so a database leak can't be used to
    take over accounts.
    """

    __tablename__ = "user_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    token_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    purpose = db.Column(db.String(32), nullable=False)
    expires_at = db.Column(db.DateTime(), nullable=False)
    used_at = db.Column(db.DateTime(), nullable=True)
    created_at = db.Column(db.DateTime(), nullable=False, default=utcnow)

    def is_valid(self) -> bool:
        return self.used_at is None and self.expires_at > utcnow()

    def __repr__(self) -> str:
        return f"<UserToken {self.purpose} user={self.user_id}>"
