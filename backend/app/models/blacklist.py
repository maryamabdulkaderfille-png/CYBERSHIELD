from app.extensions import db
from app.utils.time import utcnow


class BlacklistEntry(db.Model):
    """Known-malicious domains, managed via the admin Blacklist Management
    UI (Phase 7)."""

    __tablename__ = "blacklist_entries"

    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), nullable=False, unique=True, index=True)
    reason = db.Column(db.String(255), nullable=False, default="Reported phishing domain")
    added_by_user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime(), nullable=False, default=utcnow)
    # Disabling an entry (rather than deleting it) preserves the audit trail
    # of why a domain was once blacklisted. blacklist_check.py only matches
    # enabled=True rows.
    enabled = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "domain": self.domain,
            "reason": self.reason,
            "added_by_user_id": self.added_by_user_id,
            "created_at": f"{self.created_at.isoformat()}Z",
            "enabled": self.enabled,
        }

    def __repr__(self) -> str:
        return f"<BlacklistEntry {self.domain}>"
