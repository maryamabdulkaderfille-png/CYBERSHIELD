from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.extensions import db
from app.models.audit_log import AuditAction
from app.models.user import User
from app.schemas.user import ChangePasswordSchema, UpdateProfileSchema
from app.services import audit_service, auth_service, session_service
from app.utils.errors import APIError

users_bp = Blueprint("users", __name__)


def _current_user() -> User:
    user = db.session.get(User, get_jwt_identity())
    if user is None:
        raise APIError("User not found.", 404)
    return user


@users_bp.get("/me")
@jwt_required()
def get_me():
    return jsonify({"user": _current_user().to_public_dict()})


@users_bp.put("/me")
@jwt_required()
def update_me():
    try:
        data = UpdateProfileSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    user = auth_service.update_profile(
        _current_user(), full_name=data.get("full_name"), username=data.get("username")
    )
    return jsonify({"message": "Profile updated.", "user": user.to_public_dict()})


@users_bp.put("/me/password")
@jwt_required()
def change_password():
    try:
        data = ChangePasswordSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    auth_service.change_password(_current_user(), data["current_password"], data["new_password"])
    # Kick out every other logged-in session/device on a password change —
    # same call /settings/sessions/revoke-others already makes — while
    # leaving the current session (the one making this request) alone.
    session_service.revoke_all_other_sessions(get_jwt_identity(), current_session_key=get_jwt().get("sid"))
    audit_service.log_action(get_jwt_identity(), AuditAction.PASSWORD_CHANGED, request.remote_addr)
    return jsonify({"message": "Password updated."})
