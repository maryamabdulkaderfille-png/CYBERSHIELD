from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from app.constants import RiskLevel
from app.services.unified_scan_service import RANGE_KEYS, SCANNER_TYPES


class UnifiedScanQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=10, validate=validate.Range(min=1, max=50))
    scanner_type = fields.String(load_default=None, allow_none=True, validate=validate.OneOf(SCANNER_TYPES))
    risk_level = fields.String(load_default=None, allow_none=True, validate=validate.OneOf(RiskLevel.ALL))
    search = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=2048))
    trust_score_min = fields.Integer(load_default=None, allow_none=True, validate=validate.Range(min=0, max=100))
    trust_score_max = fields.Integer(load_default=None, allow_none=True, validate=validate.Range(min=0, max=100))
    date_from = fields.DateTime(load_default=None, allow_none=True)
    date_to = fields.DateTime(load_default=None, allow_none=True)
    source = fields.String(load_default=None, allow_none=True, validate=validate.OneOf(["web", "extension"]))
    sort_by = fields.String(load_default="scan_date", validate=validate.OneOf(["scan_date", "trust_score"]))
    sort_dir = fields.String(load_default="desc", validate=validate.OneOf(["asc", "desc"]))

    @validates_schema
    def _validate_ranges(self, data, **kwargs):
        lo, hi = data.get("trust_score_min"), data.get("trust_score_max")
        if lo is not None and hi is not None and lo > hi:
            raise ValidationError("trust_score_min must not be greater than trust_score_max.")

        date_from, date_to = data.get("date_from"), data.get("date_to")
        if date_from is not None and date_to is not None and date_from > date_to:
            raise ValidationError("date_from must not be after date_to.")


class RangeQuerySchema(Schema):
    range = fields.String(load_default="30d", validate=validate.OneOf(RANGE_KEYS))


class BulkDeleteSchema(Schema):
    items = fields.List(
        fields.Dict(),
        required=True,
        validate=validate.Length(min=1, max=100),
    )

    @validates_schema
    def _validate_items(self, data, **kwargs):
        for item in data.get("items", []):
            if "scanner_type" not in item or "id" not in item:
                raise ValidationError("Each item must include 'scanner_type' and 'id'.")
            if item["scanner_type"] not in SCANNER_TYPES:
                raise ValidationError(f"Invalid scanner_type: {item['scanner_type']}")
