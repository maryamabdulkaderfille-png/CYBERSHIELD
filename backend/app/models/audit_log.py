from sqlalchemy.dialects.postgresql import JSONB

from app.extensions import db
from app.utils.time import utcnow

# Plain JSON on SQLite (tests), JSONB on Postgres — see app.models.scan for
# the same rationale.
_JSON_VARIANT = db.JSON().with_variant(JSONB, "postgresql")


class AuditAction:
    LOGIN = "login"
    LOGOUT = "logout"
    PROFILE_UPDATE = "profile_update"
    SETTINGS_UPDATE = "settings_update"
    ADMIN_ACTION = "admin_action"
    BLACKLIST_UPDATE = "blacklist_update"
    RULE_CHANGE = "rule_change"
    EXTENSION_EVENT = "extension_event"
    REPORT_GENERATED = "report_generated"
    SCAN_DELETED = "scan_deleted"
    WEBSITE_REPORTED = "website_reported"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    PASSWORD_CHANGED = "password_changed"
    BLOCKLIST_ADD = "blocklist_add"
    BLOCKLIST_REMOVE = "blocklist_remove"
    EMAIL_VERIFICATION_SENT = "email_verification_sent"
    ALL = (
        LOGIN,
        LOGOUT,
        PROFILE_UPDATE,
        SETTINGS_UPDATE,
        ADMIN_ACTION,
        BLACKLIST_UPDATE,
        RULE_CHANGE,
        EXTENSION_EVENT,
        REPORT_GENERATED,
        SCAN_DELETED,
        WEBSITE_REPORTED,
        PASSWORD_RESET_REQUESTED,
        PASSWORD_RESET_COMPLETED,
        PASSWORD_CHANGED,
        BLOCKLIST_ADD,
        BLOCKLIST_REMOVE,
        EMAIL_VERIFICATION_SENT,
    )


class AuditStatus:
    SUCCESS = "success"
    FAILURE = "failure"
    ALL = (SUCCESS, FAILURE)


class AuditLog(db.Model):
    """Append-only security/activity log (Phase 7). Nullable `user_id` covers
    events where identity isn't yet known (e.g. a failed login attempt for
    an email that doesn't match any account)."""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True, index=True)
    action = db.Column(db.String(32), nullable=False, index=True)
    status = db.Column(db.String(16), nullable=False, default=AuditStatus.SUCCESS)
    ip_address = db.Column(db.String(64), nullable=True)
    # Small, non-sensitive context (e.g. {"target_user_id": "...", "field": "email"}).
    # Never used to store passwords/tokens/PII beyond what's already public.
    details = db.Column(_JSON_VARIANT, nullable=True)
    created_at = db.Column(db.DateTime(), nullable=False, default=utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "status": self.status,
            "ip_address": self.ip_address,
            "details": self.details,
            "created_at": f"{self.created_at.isoformat()}Z",
        }
