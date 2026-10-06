from app.extensions import db
from app.models.user_settings import UserSettings

UPDATABLE_FIELDS = (
    "theme",
    "language",
    "timezone",
    "notify_high_risk_url",
    "notify_dangerous_email",
    "notify_qr_threat",
    "notify_weekly_summary",
    "profile_visibility",
    "protection_mode",
)


def get_or_create_settings(user_id: str) -> UserSettings:
    settings = db.session.get(UserSettings, user_id)
    if settings is None:
        settings = UserSettings(user_id=user_id)
        db.session.add(settings)
        db.session.commit()
    return settings


def update_settings(user_id: str, data: dict) -> UserSettings:
    settings = get_or_create_settings(user_id)
    # Explicit allow-list, not `for k, v in data.items(): setattr(...)` —
    # the schema already restricts `data` to known fields, but this is a
    # second, independent guard against mass assignment if that ever changes.
    for field in UPDATABLE_FIELDS:
        if field in data:
            setattr(settings, field, data[field])
    db.session.commit()
    return settings
