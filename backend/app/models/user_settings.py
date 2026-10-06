from app.extensions import db
from app.utils.time import utcnow


class Theme:
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"
    ALL = (DARK, LIGHT, SYSTEM)


class ProfileVisibility:
    PRIVATE = "private"
    PUBLIC = "public"
    ALL = (PRIVATE, PUBLIC)


class ProtectionMode:
    """Active Protection (Phase 9) — governs how the browser extension reacts
    to a Dangerous (or Dangerous+Suspicious) scan result. WARN_ONLY preserves
    the exact Phase 6 behavior (a dismissible warning overlay); the auto-block
    modes additionally add the site to the user's Personal Block List and
    enforce a non-dismissible block on future visits."""

    WARN_ONLY = "warn_only"
    ASK_BEFORE_BLOCKING = "ask_before_blocking"
    AUTO_BLOCK_DANGEROUS = "auto_block_dangerous"
    AUTO_BLOCK_DANGEROUS_SUSPICIOUS = "auto_block_dangerous_suspicious"
    ALL = (WARN_ONLY, ASK_BEFORE_BLOCKING, AUTO_BLOCK_DANGEROUS, AUTO_BLOCK_DANGEROUS_SUSPICIOUS)


class UserSettings(db.Model):
    """One-to-one with User. Created lazily on first access (see
    user_settings_service.get_or_create_settings) rather than at
    registration, so Phase 1's registration flow is untouched."""

    __tablename__ = "user_settings"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), primary_key=True)
    theme = db.Column(db.String(16), nullable=False, default=Theme.SYSTEM)
    language = db.Column(db.String(8), nullable=False, default="en")
    timezone = db.Column(db.String(64), nullable=False, default="UTC")

    notify_high_risk_url = db.Column(db.Boolean, nullable=False, default=True)
    notify_dangerous_email = db.Column(db.Boolean, nullable=False, default=True)
    notify_qr_threat = db.Column(db.Boolean, nullable=False, default=True)
    notify_weekly_summary = db.Column(db.Boolean, nullable=False, default=True)

    profile_visibility = db.Column(db.String(16), nullable=False, default=ProfileVisibility.PRIVATE)

    protection_mode = db.Column(db.String(32), nullable=False, default=ProtectionMode.WARN_ONLY)

    created_at = db.Column(db.DateTime(), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(), nullable=False, default=utcnow, onupdate=utcnow)

    def to_dict(self) -> dict:
        return {
            "theme": self.theme,
            "language": self.language,
            "timezone": self.timezone,
            "notify_high_risk_url": self.notify_high_risk_url,
            "notify_dangerous_email": self.notify_dangerous_email,
            "notify_qr_threat": self.notify_qr_threat,
            "notify_weekly_summary": self.notify_weekly_summary,
            "profile_visibility": self.profile_visibility,
            "protection_mode": self.protection_mode,
        }
