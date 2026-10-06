from sqlalchemy.dialects.postgresql import JSONB

from app.extensions import db
from app.utils.time import utcnow

# Plain JSON on SQLite (tests), JSONB on Postgres — see app.models.scan for
# the same rationale.
_JSON_VARIANT = db.JSON().with_variant(JSONB, "postgresql")


class EmailScanHistory(db.Model):
    __tablename__ = "email_scan_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    sender_display_name = db.Column(db.String(255), nullable=True)
    sender_email = db.Column(db.String(255), nullable=True, index=True)
    subject = db.Column(db.String(998), nullable=True)  # RFC 5322 max header line length
    trust_score = db.Column(db.Integer, nullable=False)
    risk_level = db.Column(db.String(16), nullable=False, index=True)
    link_count = db.Column(db.Integer, nullable=False, default=0)
    attachment_count = db.Column(db.Integer, nullable=False, default=0)
    scan_result = db.Column(_JSON_VARIANT, nullable=False)
    analysis_details = db.Column(_JSON_VARIANT, nullable=False)
    scan_date = db.Column(db.DateTime(), nullable=False, default=utcnow, index=True)
    duration_ms = db.Column(db.Integer, nullable=True)
    # Always "web" today (no extension integration for email scans yet) —
    # present for schema parity with ScanHistory in the unified Scan Center
    # UNION ALL query.
    source = db.Column(db.String(16), nullable=False, default="web")

    def to_summary_dict(self) -> dict:
        return {
            "id": self.id,
            "sender_display_name": self.sender_display_name,
            "sender_email": self.sender_email,
            "subject": self.subject,
            "trust_score": self.trust_score,
            "risk_level": self.risk_level,
            "link_count": self.link_count,
            "attachment_count": self.attachment_count,
            "scan_date": f"{self.scan_date.isoformat()}Z",
        }

    def to_detail_dict(self) -> dict:
        return {
            "id": self.id,
            "sender_display_name": self.scan_result["sender_display_name"],
            "sender_email": self.scan_result["sender_email"],
            "subject": self.scan_result["subject"],
            "trust_score": self.scan_result["trust_score"],
            "risk": self.scan_result["risk"],
            "reasons": self.scan_result["reasons"],
            "recommendations": self.scan_result["recommendations"],
            "links": self.scan_result["links"],
            "attachments": self.scan_result["attachments"],
            "rules": self.analysis_details["rules"],
            "scan_date": f"{self.scan_date.isoformat()}Z",
        }

    def __repr__(self) -> str:
        return f"<EmailScanHistory {self.sender_email} score={self.trust_score}>"
