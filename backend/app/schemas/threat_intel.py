from marshmallow import Schema, fields, validate

from app.constants import RiskLevel


class ThreatDomainQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=20, validate=validate.Range(min=1, max=50))
    search = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=255))
    risk_level = fields.String(load_default=None, allow_none=True, validate=validate.OneOf(RiskLevel.ALL))
    sort_by = fields.String(load_default="count", validate=validate.OneOf(["count", "last_seen", "domain"]))
    sort_dir = fields.String(load_default="desc", validate=validate.OneOf(["asc", "desc"]))
