from marshmallow import Schema, ValidationError, fields, validate, validates, validates_schema

from app.models.audit_log import AuditAction, AuditStatus
from app.models.user import UserRole, UserStatus
from app.models.user_restriction import RestrictableFeature


class AdminUserQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))
    search = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=255))
    role = fields.String(load_default=None, allow_none=True, validate=validate.OneOf(UserRole.ALL))
    is_active = fields.Boolean(load_default=None, allow_none=True)
    status = fields.String(load_default=None, allow_none=True, validate=validate.OneOf(UserStatus.ALL))


class AdminUserStatusSchema(Schema):
    status = fields.String(required=True, validate=validate.OneOf(UserStatus.ALL))


class AdminUserRestrictionSchema(Schema):
    feature = fields.String(required=True, validate=validate.OneOf(RestrictableFeature.ALL))


class AdminBlacklistQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))
    search = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=255))
    enabled = fields.Boolean(load_default=None, allow_none=True)


_MAX_REASON_LENGTH = 255
_MAX_DOMAIN_LENGTH = 255


class AdminBlacklistAddSchema(Schema):
    domain = fields.String(required=True, validate=validate.Length(min=3, max=_MAX_DOMAIN_LENGTH))
    reason = fields.String(load_default="Reported phishing domain", validate=validate.Length(max=_MAX_REASON_LENGTH))

    @validates("domain")
    def _validate_domain(self, value, **kwargs):
        candidate = value.strip().lower()
        if " " in candidate or "/" in candidate:
            raise ValidationError("Enter a bare domain, e.g. 'example.com' — not a full URL.")
        if "." not in candidate:
            raise ValidationError("Enter a valid domain.")


class AdminRuleToggleSchema(Schema):
    enabled = fields.Boolean(required=True)


class AdminAuditQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=25, validate=validate.Range(min=1, max=100))
    action = fields.String(load_default=None, allow_none=True, validate=validate.OneOf(AuditAction.ALL))
    user_id = fields.String(load_default=None, allow_none=True)
    status = fields.String(load_default=None, allow_none=True, validate=validate.OneOf(AuditStatus.ALL))
    search = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=255))
    date_from = fields.DateTime(load_default=None, allow_none=True)
    date_to = fields.DateTime(load_default=None, allow_none=True)

    @validates_schema
    def _validate_date_range(self, data, **kwargs):
        if data.get("date_from") and data.get("date_to") and data["date_from"] > data["date_to"]:
            raise ValidationError("date_from must be before date_to.", field_name="date_from")
