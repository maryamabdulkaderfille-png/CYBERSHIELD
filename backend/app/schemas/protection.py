from marshmallow import Schema, fields, validate

from app.constants import RiskLevel

_MAX_TARGET_LENGTH = 2048
_MAX_REASON_LENGTH = 500


class BlockListQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))
    search = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=255))
    risk_level = fields.String(load_default=None, allow_none=True, validate=validate.OneOf(RiskLevel.ALL))
    is_active = fields.Boolean(load_default=True, allow_none=True)
    sort_by = fields.String(load_default="blocked_at", validate=validate.OneOf(["blocked_at", "domain", "trust_score"]))
    sort_dir = fields.String(load_default="desc", validate=validate.OneOf(["asc", "desc"]))


class BlockWebsiteSchema(Schema):
    """Target can be a bare domain or a full URL — block_list_service
    normalizes either into a registrable domain, same as the admin
    blacklist's "reject full URLs" schema chooses NOT to do, since here the
    input is coming straight off an existing scan result the user already
    has in front of them (their own URL, not a fresh admin-typed domain)."""

    target = fields.String(required=True, validate=validate.Length(min=1, max=_MAX_TARGET_LENGTH))
    trust_score = fields.Integer(required=True, validate=validate.Range(min=0, max=100))
    risk_level = fields.String(required=True, validate=validate.OneOf(RiskLevel.ALL))
    reasons = fields.List(fields.String(validate=validate.Length(max=_MAX_REASON_LENGTH)), load_default=list)
    scanner_type = fields.String(load_default="url", validate=validate.OneOf(["url", "email", "qr"]))
    scan_id = fields.Integer(load_default=None, allow_none=True)


class ReportWebsiteSchema(Schema):
    target = fields.String(required=True, validate=validate.Length(min=1, max=_MAX_TARGET_LENGTH))
    reasons = fields.List(fields.String(validate=validate.Length(max=_MAX_REASON_LENGTH)), load_default=list)


class ExplainRequestSchema(Schema):
    risk = fields.String(required=True, validate=validate.OneOf(RiskLevel.ALL))
    trust_score = fields.Integer(required=True, validate=validate.Range(min=0, max=100))
    reasons = fields.List(fields.String(), load_default=list)
    rules = fields.List(fields.Dict(), load_default=list)


class CommunityQuerySchema(Schema):
    domains = fields.String(required=True, validate=validate.Length(min=1, max=4096))


class ExtensionBlockedEventSchema(Schema):
    domain = fields.String(required=True, validate=validate.Length(min=1, max=255))
