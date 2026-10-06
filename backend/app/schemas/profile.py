import re

from marshmallow import Schema, ValidationError, fields, validate, validates

_PHONE_RE = re.compile(r"^[0-9+\-\s()]{5,32}$")
_COUNTRY_RE = re.compile(r"^[A-Z]{2}$")


class UpdateExtendedProfileSchema(Schema):
    """Extended profile fields only (phone/country/bio/avatar_url) — separate
    from UpdateProfileSchema (full_name/username) so /profile doesn't
    duplicate what /users/me already updates. Only these four fields are
    declared, so marshmallow's default unknown="raise" rejects anything else,
    same as the existing mass-assignment guard on UpdateProfileSchema."""

    phone = fields.String(required=False, allow_none=True, validate=validate.Length(max=32))
    country = fields.String(required=False, allow_none=True, validate=validate.Length(equal=2))
    bio = fields.String(required=False, allow_none=True, validate=validate.Length(max=500))
    avatar_url = fields.Url(required=False, allow_none=True, validate=validate.Length(max=1024))

    @validates("phone")
    def _validate_phone(self, value, **kwargs):
        if value and not _PHONE_RE.match(value):
            raise ValidationError("Phone number contains invalid characters.")

    @validates("country")
    def _validate_country(self, value, **kwargs):
        if value and not _COUNTRY_RE.match(value.upper()):
            raise ValidationError("Country must be a 2-letter ISO 3166-1 alpha-2 code.")
