from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError

from app.extensions import limiter
from app.models.audit_log import AuditAction
from app.models.user_restriction import RestrictableFeature
from app.rbac import require_permission
from app.schemas.admin import AdminUserQuerySchema, AdminUserRestrictionSchema, AdminUserStatusSchema
from app.services import admin_user_service, audit_service, user_restriction_service
from app.utils.errors import APIError

admin_users_bp = Blueprint("admin_users", __name__)


@admin_users_bp.get("")
@require_permission("users.view")
def list_users():
    try:
        params = AdminUserQuerySchema().load(request.args.to_dict())
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    items, total = admin_user_service.list_users(
        params["page"], params["per_page"], params["search"], params["role"], params["is_active"], params["status"]
    )
    return jsonify(
        {
            "items": [u.to_public_dict() for u in items],
            "page": params["page"],
            "per_page": params["per_page"],
            "total": total,
            "total_pages": max(1, (total + params["per_page"] - 1) // params["per_page"]),
        }
    )


@admin_users_bp.get("/<user_id>")
@require_permission("users.view")
def get_user_detail(user_id: str):
    return jsonify(admin_user_service.get_user_detail(user_id))


@admin_users_bp.get("/<user_id>/activity")
@require_permission("users.view")
def get_user_activity(user_id: str):
    return jsonify({"items": admin_user_service.get_user_recent_activity(user_id)})


@admin_users_bp.post("/<user_id>/deactivate")
@limiter.limit("30 per minute")
@require_permission("users.manage")
def deactivate_user(user_id: str):
    if user_id == get_jwt_identity():
        raise APIError("You cannot deactivate your own account from the admin panel.", 400)

    user = admin_user_service.deactivate_user(user_id)
    audit_service.log_action(
        get_jwt_identity(), AuditAction.ADMIN_ACTION, request.remote_addr,
        action_detail="deactivate_user", target_user_id=user_id,
    )
    return jsonify({"message": "User deactivated.", "user": user.to_public_dict()})


@admin_users_bp.post("/<user_id>/reactivate")
@limiter.limit("30 per minute")
@require_permission("users.manage")
def reactivate_user(user_id: str):
    user = admin_user_service.reactivate_user(user_id)
    audit_service.log_action(
        get_jwt_identity(), AuditAction.ADMIN_ACTION, request.remote_addr,
        action_detail="reactivate_user", target_user_id=user_id,
    )
    return jsonify({"message": "User reactivated.", "user": user.to_public_dict()})


@admin_users_bp.post("/<user_id>/reset-password")
@limiter.limit("30 per minute")
@require_permission("users.manage")
def reset_password_placeholder(user_id: str):
    raise APIError("Admin-triggered password reset is not yet implemented in this version of CyberShield.", 501)


@admin_users_bp.patch("/<user_id>/status")
@limiter.limit("30 per minute")
@require_permission("users.manage")
def update_user_status(user_id: str):
    if user_id == get_jwt_identity():
        raise APIError("You cannot change your own account status from the admin panel.", 400)

    try:
        data = AdminUserStatusSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    old_status = admin_user_service.get_user_or_404(user_id).status
    user = admin_user_service.set_user_status(user_id, data["status"])
    audit_service.log_action(
        get_jwt_identity(), AuditAction.ADMIN_ACTION, request.remote_addr,
        action_detail="user_status_change", target_user_id=user_id,
        old_status=old_status, new_status=data["status"],
    )
    return jsonify({"message": f"User status set to '{data['status']}'.", "user": user.to_public_dict()})


@admin_users_bp.get("/<user_id>/restrictions")
@require_permission("users.view")
def list_user_restrictions(user_id: str):
    admin_user_service.get_user_or_404(user_id)
    restrictions = user_restriction_service.list_restrictions(user_id)
    return jsonify({"items": [r.to_dict() for r in restrictions]})


@admin_users_bp.post("/<user_id>/restrictions")
@limiter.limit("30 per minute")
@require_permission("users.manage")
def add_user_restriction(user_id: str):
    admin_user_service.get_user_or_404(user_id)
    try:
        data = AdminUserRestrictionSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    restriction = user_restriction_service.add_restriction(user_id, data["feature"], get_jwt_identity())
    audit_service.log_action(
        get_jwt_identity(), AuditAction.ADMIN_ACTION, request.remote_addr,
        action_detail="restriction_added", target_user_id=user_id, feature=data["feature"],
    )
    return jsonify({"message": "Restriction added.", "restriction": restriction.to_dict()}), 201


@admin_users_bp.delete("/<user_id>/restrictions/<feature>")
@limiter.limit("30 per minute")
@require_permission("users.manage")
def remove_user_restriction(user_id: str, feature: str):
    admin_user_service.get_user_or_404(user_id)
    if feature not in RestrictableFeature.ALL:
        raise APIError(f"Unknown feature: {feature}", 422)

    removed = user_restriction_service.remove_restriction(user_id, feature)
    if not removed:
        raise APIError("That restriction does not exist.", 404)

    audit_service.log_action(
        get_jwt_identity(), AuditAction.ADMIN_ACTION, request.remote_addr,
        action_detail="restriction_removed", target_user_id=user_id, feature=feature,
    )
    return jsonify({"message": "Restriction removed."})
