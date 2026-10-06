from sqlalchemy.dialects.postgresql import JSONB

from app.extensions import db
from app.utils.time import utcnow

# Plain JSON on SQLite (tests), JSONB on Postgres — see app.models.scan for
# the same rationale.
_JSON_VARIANT = db.JSON().with_variant(JSONB, "postgresql")


class QRScanHistory(db.Model):
    __tablename__ = "qr_scan_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    content_type = db.Column(db.String(32), nullable=False, index=True)
    raw_content = db.Column(db.String(2048), nullable=False)
    trust_score = db.Column(db.Integer, nullable=False)
    risk_level = db.Column(db.String(16), nullable=False, index=True)
    scan_result = db.Column(_JSON_VARIANT, nullable=False)
    analysis_details = db.Column(_JSON_VARIANT, nullable=False)
    scan_date = db.Column(db.DateTime(), nullable=False, default=utcnow, index=True)
    duration_ms = db.Column(db.Integer, nullable=True)
    # Always "web" today (no extension integration for QR scans) — present
    # for schema parity with ScanHistory in the unified Scan Center query.
    source = db.Column(db.String(16), nullable=False, default="web")

    def to_summary_dict(self) -> dict:
        return {
            "id": self.id,
            "content_type": self.content_type,
            "raw_content": self.raw_content,
            "trust_score": self.trust_score,
            "risk_level": self.risk_level,
            "scan_date": f"{self.scan_date.isoformat()}Z",
        }

    def to_detail_dict(self) -> dict:
        return {
            "id": self.id,
            "content_type": self.scan_result["content_type"],
            "raw_content": self.scan_result["raw_content"],
            "parsed_fields": self.scan_result["parsed_fields"],
            "trust_score": self.scan_result["trust_score"],
            "risk": self.scan_result["risk"],
            "reasons": self.scan_result["reasons"],
            "recommendations": self.scan_result["recommendations"],
            "rules": self.analysis_details["rules"],
            "scan_date": f"{self.scan_date.isoformat()}Z",
        }

    def __repr__(self) -> str:
        return f"<QRScanHistory {self.content_type} score={self.trust_score}>"
