from sqlalchemy.dialects.postgresql import JSONB

from app.constants import RiskLevel
from app.extensions import db
from app.utils.time import utcnow

# Kept as an alias: existing code (schemas, tests) imports RiskLevelChoices from
# here. The canonical definition lives in app.constants so both this module and
# app.services.url_scanner can depend on it without a circular import.
RiskLevelChoices = RiskLevel

#  Plain JSON on SQLite (used in tests), JSONB on Postgres — smaller on disk,
# indexable, and directly queryable (e.g. `scan_result['risk']`) in production.
_JSON_VARIANT = db.JSON().with_variant(JSONB, "postgresql")


class ScanHistory(db.Model):
    __tablename__ = "scan_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    url = db.Column(db.String(2048), nullable=False)
    trust_score = db.Column(db.Integer, nullable=False)
    risk_level = db.Column(db.String(16), nullable=False, index=True)
    scan_result = db.Column(_JSON_VARIANT, nullable=False)
    analysis_details = db.Column(_JSON_VARIANT, nullable=False)
    scan_date = db.Column(db.DateTime(), nullable=False, default=utcnow, index=True)
    # Nullable: only populated for scans run after this column was added —
    # "Average Scan Duration" (Phase 5) averages over non-null rows only,
    # never backfilled/fabricated for older scans.
    duration_ms = db.Column(db.Integer, nullable=True)
    # "web" (dashboard URL Scanner) or "extension" (Phase 6 browser
    # extension's default, persisting scan path) — set by the route from
    # the request's client header, never inferred/guessed after the fact.
    source = db.Column(db.String(16), nullable=False, default="web")

    def to_summary_dict(self) -> dict:
        return {
            "id": self.id,
            "url": self.url,
            "trust_score": self.trust_score,
            "risk_level": self.risk_level,
            "scan_date": f"{self.scan_date.isoformat()}Z",
        }

    def to_detail_dict(self) -> dict:
        """The full API response shape for a single scan: summary fields plus
        the reasons/recommendations/rule breakdown. Used for both the scan
        creation response and the scan detail endpoint."""
        return {
            "id": self.id,
            "url": self.url,
            "trust_score": self.scan_result["trust_score"],
            "risk": self.scan_result["risk"],
            "reasons": self.scan_result["reasons"],
            "recommendations": self.scan_result["recommendations"],
            "rules": self.analysis_details["rules"],
            "scan_date": f"{self.scan_date.isoformat()}Z",
        }

    def __repr__(self) -> str:
        return f"<ScanHistory {self.url} score={self.trust_score}>"
