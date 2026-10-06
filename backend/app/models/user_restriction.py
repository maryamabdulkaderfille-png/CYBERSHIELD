from app.extensions import db
from app.utils.time import utcnow


class RestrictableFeature:
    """Matches unified_scan_service's existing scanner_type vocabulary
    ("url"/"email"/"qr") rather than inventing a second naming scheme —
    a "url" restriction also gates POST /extension/scan, since it's the
    same underlying capability. "reports" is independent of scanner type:
    it gates all of /reports/*, not just one scanner's reports."""

    URL = "url"
    EMAIL = "email"
    QR = "qr"
    REPORTS = "reports"
    ALL = (URL, EMAIL, QR, REPORTS)


class UserRestriction(db.Model):
    """Per-user feature restriction, set by an admin. One row per
    (user_id, feature) pair — presence of a row means that feature is
    blocked for that user; removing the row lifts the restriction. Every
    scan/report endpoint this gates checks it server-side (see
    user_restriction_service.require_not_restricted), not just the frontend.
    """

    __tablename__ = "user_restrictions"
    __table_args__ = (db.UniqueConstraint("user_id", "feature", name="uq_user_restrictions_user_feature"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    feature = db.Column(db.String(16), nullable=False)
    restricted_by_user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    restricted_at = db.Column(db.DateTime(), nullable=False, default=utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "feature": self.feature,
            "restricted_by_user_id": self.restricted_by_user_id,
            "restricted_at": f"{self.restricted_at.isoformat()}Z",
        }

    def __repr__(self) -> str:
        return f"<UserRestriction user={self.user_id} feature={self.feature}>"
