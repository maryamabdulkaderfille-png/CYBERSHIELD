from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.extensions import db, limiter
from app.models.audit_log import AuditAction
from app.models.notification import NotificationType
from app.models.user import User
from app.schemas.settings import DeactivateAccountSchema, UpdateSettingsSchema
from app.services import audit_service, auth_service, notification_service, session_service, user_settings_service
from app.utils.errors import APIError

settings_bp = Blueprint("settings", __name__)


@settings_bp.get("")
@jwt_required()
def get_settings():
    settings = user_settings_service.get_or_create_settings(get_jwt_identity())
    return jsonify({"settings": settings.to_dict()})


@settings_bp.put("")
@jwt_required()
def update_settings():
    try:
        data = UpdateSettingsSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    user_id = get_jwt_identity()
    settings = user_settings_service.update_settings(user_id, data)
    audit_service.log_action(user_id, AuditAction.SETTINGS_UPDATE, request.remote_addr, fields=list(data.keys()))
    if "protection_mode" in data:
        notification_service.create_notification(
            user_id=user_id,
            notif_type=NotificationType.PROTECTION_MODE_CHANGED,
            title="Protection mode changed",
            message=f"Active Protection is now set to '{data['protection_mode'].replace('_', ' ')}'.",
        )
    return jsonify({"message": "Settings updated.", "settings": settings.to_dict()})


@settings_bp.get("/sessions")
@jwt_required()
def list_sessions():
    current_session_key = get_jwt().get("sid")
    sessions = session_service.list_sessions(get_jwt_identity())
    return jsonify({"sessions": [s.to_dict(current_session_key=current_session_key) for s in sessions]})


@settings_bp.delete("/sessions/<int:session_id>")
@jwt_required()
def revoke_session(session_id: int):
    revoked = session_service.revoke_session(get_jwt_identity(), session_id)
    if not revoked:
        raise APIError("Session not found.", 404)
    return jsonify({"message": "Session revoked."})


@settings_bp.post("/sessions/revoke-others")
@jwt_required()
def revoke_other_sessions():
    revoked_count = session_service.revoke_all_other_sessions(get_jwt_identity(), get_jwt().get("sid"))
    return jsonify({"message": f"{revoked_count} other session(s) revoked.", "revoked_count": revoked_count})


@settings_bp.delete("/account")
@limiter.limit("3 per minute")
@jwt_required()
def deactivate_account():
    try:
        data = DeactivateAccountSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    user = db.session.get(User, get_jwt_identity())
    if user is None:
        raise APIError("User not found.", 404)

    auth_service.deactivate_account(user, data["password"])

    claims = get_jwt()
    auth_service.revoke_token(
        jti=claims["jti"],
        token_type=claims.get("type", "access"),
        user_id=user.id,
        expires_at=datetime.fromtimestamp(claims["exp"], tz=timezone.utc).replace(tzinfo=None),
    )
    # Deactivation should end every session, including this one — unlike
    # "revoke others", there is no session to spare here.
    session_service.revoke_all_other_sessions(user.id, current_session_key=None)

    return jsonify({"message": "Account deactivated."})


@settings_bp.get("/export")
@jwt_required()
def export_my_data():
    raise APIError("Data export is not yet implemented in this version of CyberShield.", 501)
