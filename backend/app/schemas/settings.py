from zoneinfo import available_timezones

from marshmallow import Schema, ValidationError, fields, validate, validates

from app.models.user_settings import ProfileVisibility, ProtectionMode, Theme

_VALID_TIMEZONES = available_timezones()


class UpdateSettingsSchema(Schema):
    """Field set mirrors user_settings_service.UPDATABLE_FIELDS exactly —
    only these are ever written to the row (mass-assignment guard)."""

    theme = fields.String(required=False, validate=validate.OneOf(Theme.ALL))
    language = fields.String(required=False, validate=validate.Length(min=2, max=8))
    timezone = fields.String(required=False, validate=validate.Length(min=1, max=64))

    @validates("timezone")
    def _validate_timezone(self, value, **kwargs):
        if value not in _VALID_TIMEZONES:
            raise ValidationError("Must be a valid IANA timezone name (e.g. 'America/New_York').")
    notify_high_risk_url = fields.Boolean(required=False)
    notify_dangerous_email = fields.Boolean(required=False)
    notify_qr_threat = fields.Boolean(required=False)
    notify_weekly_summary = fields.Boolean(required=False)
    profile_visibility = fields.String(required=False, validate=validate.OneOf(ProfileVisibility.ALL))
    protection_mode = fields.String(required=False, validate=validate.OneOf(ProtectionMode.ALL))


class DeactivateAccountSchema(Schema):
    password = fields.String(required=True, load_only=True)
