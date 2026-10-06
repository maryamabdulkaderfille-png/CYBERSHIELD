from sqlalchemy.dialects.postgresql import JSONB

from app.extensions import db
from app.utils.time import utcnow

# Plain JSON on SQLite (tests), JSONB on Postgres — see app.models.scan for
# the same rationale.
_JSON_VARIANT = db.JSON().with_variant(JSONB, "postgresql")


class BlockedWebsite(db.Model):
    """A user's Personal Block List entry (Phase 9). Created from a Dangerous
    URL scan result (`scan_id`/`scanner_type` point back to it — same
    compound-key spirit as the Scan Center) via the "Block Website" action,
    or automatically by the browser extension when Active Protection is set
    to an auto-block mode.

    Soft-deletable: `is_active=False` + `unblocked_at` set is "Remove" (the
    row stays so "Restore" can reactivate it and re-blocking the same domain
    reuses the row instead of violating the uniqueness constraint below).
    """

    __tablename__ = "blocked_websites"
    __table_args__ = (db.UniqueConstraint("user_id", "domain", name="uq_blocked_websites_user_domain"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    domain = db.Column(db.String(255), nullable=False, index=True)
    trust_score = db.Column(db.Integer, nullable=False)
    risk_level = db.Column(db.String(16), nullable=False)
    reasons = db.Column(_JSON_VARIANT, nullable=False, default=list)
    scanner_type = db.Column(db.String(16), nullable=False, default="url")
    scan_id = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    blocked_at = db.Column(db.DateTime(), nullable=False, default=utcnow)
    unblocked_at = db.Column(db.DateTime(), nullable=True)
    created_at = db.Column(db.DateTime(), nullable=False, default=utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "domain": self.domain,
            "trust_score": self.trust_score,
            "risk_level": self.risk_level,
            "reasons": self.reasons or [],
            "scanner_type": self.scanner_type,
            "scan_id": self.scan_id,
            "is_active": self.is_active,
            "blocked_at": f"{self.blocked_at.isoformat()}Z",
            "unblocked_at": f"{self.unblocked_at.isoformat()}Z" if self.unblocked_at else None,
        }

    def __repr__(self) -> str:
        return f"<BlockedWebsite {self.domain} user={self.user_id} active={self.is_active}>"
