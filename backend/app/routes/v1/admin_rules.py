from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError

from app.extensions import limiter
from app.models.audit_log import AuditAction
from app.models.detection_rule import RuleCategory
from app.rbac import require_permission
from app.schemas.admin import AdminRuleToggleSchema
from app.services import admin_rule_service, audit_service
from app.utils.errors import APIError

admin_rules_bp = Blueprint("admin_rules", __name__)


@admin_rules_bp.get("")
@require_permission("rules.manage")
def list_rules():
    category = request.args.get("category")
    if category and category not in RuleCategory.ALL:
        raise APIError(f"Unknown rule category: {category}", 422)

    rules = admin_rule_service.list_rules(category)
    return jsonify({"items": [r.to_dict() for r in rules]})


@admin_rules_bp.put("/<int:rule_id>")
@limiter.limit("30 per minute")
@require_permission("rules.manage")
def toggle_rule(rule_id: int):
    try:
        data = AdminRuleToggleSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    rule = admin_rule_service.set_enabled(rule_id, data["enabled"])
    audit_service.log_action(
        get_jwt_identity(), AuditAction.RULE_CHANGE, request.remote_addr,
        rule_key=rule.key, enabled=rule.enabled, version=rule.version,
    )
    return jsonify({"message": "Rule updated.", "rule": rule.to_dict()})
