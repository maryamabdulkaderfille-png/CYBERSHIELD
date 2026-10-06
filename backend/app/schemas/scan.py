from urllib.parse import urlparse

from marshmallow import Schema, ValidationError, fields, validate, validates

from app.models.scan import RiskLevelChoices

MAX_URL_LENGTH = 2048

# Control characters (including \r, \n, tab) are never legitimate in a URL and
# are a classic header/log-injection or URL-parser-confusion vector.
_CONTROL_CHARS = {chr(c) for c in range(0x00, 0x20)} | {chr(0x7F)}


def validate_scannable_url(value: str) -> None:
    value = value.strip()
    if not value:
        raise ValidationError("URL is required.")
    if len(value) > MAX_URL_LENGTH:
        raise ValidationError(f"URL is too long (max {MAX_URL_LENGTH} characters).")
    if any(char in _CONTROL_CHARS for char in value):
        raise ValidationError("URL must not contain control characters.")
    if " " in value:
        raise ValidationError("URL must not contain spaces.")

    try:
        parsed = urlparse(value)
    except ValueError as exc:
        raise ValidationError(f"URL could not be parsed: {exc}") from exc

    if parsed.scheme not in {"http", "https"}:
        raise ValidationError("URL must start with http:// or https://.")
    try:
        hostname = parsed.hostname
    except ValueError as exc:
        raise ValidationError(f"URL host is invalid: {exc}") from exc
    if not hostname:
        raise ValidationError("URL must include a valid host.")


class ScanRequestSchema(Schema):
    url = fields.String(required=True)

    @validates("url")
    def _validate_url(self, value, **kwargs):
        validate_scannable_url(value)


class ScanHistoryQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=10, validate=validate.Range(min=1, max=50))
    search = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=2048))
    risk_level = fields.String(load_default=None, allow_none=True, validate=validate.OneOf(RiskLevelChoices.ALL))
