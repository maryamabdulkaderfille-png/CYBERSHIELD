"""Extended profile view (Phase 5): adds phone/country/bio/avatar_url editing
and a stats summary on top of the existing /users/me identity endpoint,
without duplicating it — full_name/username/password updates still go
through /users/me and /users/me/password exactly as before.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.extensions import db
from app.models.audit_log import AuditAction
from app.models.user import User
from app.schemas.profile import UpdateExtendedProfileSchema
from app.services import audit_service, user_profile_service
from app.utils.errors import APIError

profile_bp = Blueprint("profile", __name__)


def _current_user() -> User:
    user = db.session.get(User, get_jwt_identity())
    if user is None:
        raise APIError("User not found.", 404)
    return user


@profile_bp.get("")
@jwt_required()
def get_profile():
    user = _current_user()
    return jsonify(
        {
            "user": user.to_public_dict(),
            "stats": user_profile_service.get_profile_stats(user.id),
        }
    )


@profile_bp.put("")
@jwt_required()
def update_profile():
    try:
        data = UpdateExtendedProfileSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    user = user_profile_service.update_profile_fields(_current_user(), data)
    audit_service.log_action(user.id, AuditAction.PROFILE_UPDATE, request.remote_addr, fields=list(data.keys()))
    return jsonify({"message": "Profile updated.", "user": user.to_public_dict()})
