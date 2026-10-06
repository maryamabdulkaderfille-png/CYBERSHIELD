from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.rbac import require_permission
from app.schemas.admin import AdminAuditQuerySchema
from app.services import audit_service

admin_audit_bp = Blueprint("admin_audit", __name__)


@admin_audit_bp.get("")
@require_permission("audit.view")
def list_audit_logs():
    try:
        params = AdminAuditQuerySchema().load(request.args.to_dict())
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    items, total = audit_service.list_audit_logs(
        params["page"],
        params["per_page"],
        params["action"],
        params["user_id"],
        params["status"],
        params["search"],
        params["date_from"],
        params["date_to"],
    )
    return jsonify(
        {
            "items": [log.to_dict() for log in items],
            "page": params["page"],
            "per_page": params["per_page"],
            "total": total,
            "total_pages": max(1, (total + params["per_page"] - 1) // params["per_page"]),
        }
    )
