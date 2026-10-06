from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError

from app.extensions import limiter
from app.models.audit_log import AuditAction
from app.rbac import require_permission
from app.schemas.admin import AdminBlacklistAddSchema, AdminBlacklistQuerySchema
from app.services import admin_blacklist_service, audit_service

admin_blacklist_bp = Blueprint("admin_blacklist", __name__)


@admin_blacklist_bp.get("")
@require_permission("blacklist.manage")
def list_entries():
    try:
        params = AdminBlacklistQuerySchema().load(request.args.to_dict())
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    items, total = admin_blacklist_service.list_entries(
        params["page"], params["per_page"], params["search"], params["enabled"]
    )
    return jsonify(
        {
            "items": [e.to_dict() for e in items],
            "page": params["page"],
            "per_page": params["per_page"],
            "total": total,
            "total_pages": max(1, (total + params["per_page"] - 1) // params["per_page"]),
        }
    )


@admin_blacklist_bp.post("")
@limiter.limit("30 per minute")
@require_permission("blacklist.manage")
def add_entry():
    try:
        data = AdminBlacklistAddSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    entry = admin_blacklist_service.add_entry(data["domain"], data["reason"], get_jwt_identity())
    audit_service.log_action(
        get_jwt_identity(), AuditAction.BLACKLIST_UPDATE, request.remote_addr,
        action_detail="add", domain=entry.domain,
    )
    return jsonify({"message": "Domain added to blacklist.", "entry": entry.to_dict()}), 201


@admin_blacklist_bp.delete("/<int:entry_id>")
@limiter.limit("30 per minute")
@require_permission("blacklist.manage")
def remove_entry(entry_id: int):
    entry = admin_blacklist_service.get_entry_or_404(entry_id)
    domain = entry.domain
    admin_blacklist_service.remove_entry(entry_id)
    audit_service.log_action(
        get_jwt_identity(), AuditAction.BLACKLIST_UPDATE, request.remote_addr,
        action_detail="remove", domain=domain,
    )
    return jsonify({"message": "Blacklist entry removed."})


@admin_blacklist_bp.put("/<int:entry_id>/enable")
@limiter.limit("30 per minute")
@require_permission("blacklist.manage")
def enable_entry(entry_id: int):
    entry = admin_blacklist_service.set_enabled(entry_id, True)
    audit_service.log_action(
        get_jwt_identity(), AuditAction.BLACKLIST_UPDATE, request.remote_addr,
        action_detail="enable", domain=entry.domain,
    )
    return jsonify({"message": "Blacklist entry enabled.", "entry": entry.to_dict()})


@admin_blacklist_bp.put("/<int:entry_id>/disable")
@limiter.limit("30 per minute")
@require_permission("blacklist.manage")
def disable_entry(entry_id: int):
    entry = admin_blacklist_service.set_enabled(entry_id, False)
    audit_service.log_action(
        get_jwt_identity(), AuditAction.BLACKLIST_UPDATE, request.remote_addr,
        action_detail="disable", domain=entry.domain,
    )
    return jsonify({"message": "Blacklist entry disabled.", "entry": entry.to_dict()})
