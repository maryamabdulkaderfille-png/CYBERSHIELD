from app.extensions import db
from app.utils.time import utcnow


class NotificationType:
    HIGH_RISK_URL = "high_risk_url"
    DANGEROUS_EMAIL = "dangerous_email"
    QR_THREAT = "qr_threat"
    REPORT_GENERATED = "report_generated"
    SECURITY_RECOMMENDATION = "security_recommendation"
    # Phase 9 — Active Protection
    WEBSITE_BLOCKED = "website_blocked"
    WEBSITE_UNBLOCKED = "website_unblocked"
    EXTENSION_BLOCKED_ACCESS = "extension_blocked_access"
    PROTECTION_MODE_CHANGED = "protection_mode_changed"
    COMMUNITY_THREAT_ALERT = "community_threat_alert"
    WEEKLY_SUMMARY = "weekly_summary"
    ALL = (
        HIGH_RISK_URL,
        DANGEROUS_EMAIL,
        QR_THREAT,
        REPORT_GENERATED,
        SECURITY_RECOMMENDATION,
        WEBSITE_BLOCKED,
        WEBSITE_UNBLOCKED,
        EXTENSION_BLOCKED_ACCESS,
        PROTECTION_MODE_CHANGED,
        COMMUNITY_THREAT_ALERT,
        WEEKLY_SUMMARY,
    )


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    type = db.Column(db.String(32), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    # Optional link back to the scan that triggered this notification —
    # same (scanner_type, id) compound-key pattern as the Scan Center.
    scanner_type = db.Column(db.String(16), nullable=True)
    scan_id = db.Column(db.Integer, nullable=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime(), nullable=False, default=utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "scanner_type": self.scanner_type,
            "scan_id": self.scan_id,
            "is_read": self.is_read,
            "created_at": f"{self.created_at.isoformat()}Z",
        }
