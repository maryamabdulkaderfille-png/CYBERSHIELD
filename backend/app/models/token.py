from app.extensions import db
from app.utils.time import utcnow


class TokenBlocklist(db.Model):
    """Revoked JWT identifiers (jti), checked on every protected request."""

    __tablename__ = "token_blocklist"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)
    token_type = db.Column(db.String(16), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False, default=utcnow)
    expires_at = db.Column(db.DateTime(), nullable=False)

    def __repr__(self) -> str:
        return f"<TokenBlocklist {self.jti}>"
