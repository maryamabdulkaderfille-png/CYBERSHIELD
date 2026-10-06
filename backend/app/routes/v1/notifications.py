from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.schemas.notification import NotificationQuerySchema
from app.services import notification_service
from app.utils.errors import APIError

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.get("")
@jwt_required()
def list_notifications():
    try:
        params = NotificationQuerySchema().load(request.args.to_dict())
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    user_id = get_jwt_identity()
    items, total = notification_service.list_notifications(
        user_id, params["page"], params["per_page"], params["unread_only"]
    )
    return jsonify(
        {
            "items": [n.to_dict() for n in items],
            "page": params["page"],
            "per_page": params["per_page"],
            "total": total,
            "total_pages": max(1, (total + params["per_page"] - 1) // params["per_page"]),
            "unread_count": notification_service.get_unread_count(user_id),
        }
    )


@notifications_bp.get("/unread-count")
@jwt_required()
def unread_count():
    return jsonify({"unread_count": notification_service.get_unread_count(get_jwt_identity())})


@notifications_bp.put("/<int:notification_id>/read")
@jwt_required()
def mark_read(notification_id: int):
    notification = notification_service.mark_read(get_jwt_identity(), notification_id)
    if notification is None:
        raise APIError("Notification not found.", 404)
    return jsonify({"message": "Notification marked as read.", "notification": notification.to_dict()})


@notifications_bp.put("/read-all")
@jwt_required()
def mark_all_read():
    updated = notification_service.mark_all_read(get_jwt_identity())
    return jsonify({"message": f"{updated} notification(s) marked as read.", "updated_count": updated})


@notifications_bp.delete("/<int:notification_id>")
@jwt_required()
def delete_notification(notification_id: int):
    deleted = notification_service.delete_notification(get_jwt_identity(), notification_id)
    if not deleted:
        raise APIError("Notification not found.", 404)
    return jsonify({"message": "Notification deleted."})
