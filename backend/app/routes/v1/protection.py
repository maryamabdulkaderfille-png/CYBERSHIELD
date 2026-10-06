"""Active Protection & Smart Blocking (Phase 9).

Reuses the existing URL detection engine's already-computed scan results
(nothing here re-scores a URL), the existing notification system
(notification_service.create_notification), the existing audit log
(audit_service.log_action), and the existing per-user JWT auth — no new
auth/RBAC concept, since this is a personal, not admin, feature.
"""

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.extensions import limiter
from app.models.audit_log import AuditAction
from app.models.notification import NotificationType
from app.schemas.protection import (
    BlockListQuerySchema,
    BlockWebsiteSchema,
    CommunityQuerySchema,
    ExplainRequestSchema,
    ExtensionBlockedEventSchema,
    ReportWebsiteSchema,
)
from app.services import audit_service, block_list_service, community_intel_service, explanation_service, notification_service, protection_service, user_settings_service
from app.utils.errors import APIError

protection_bp = Blueprint("protection", __name__)


@protection_bp.get("/blocklist")
@jwt_required()
def list_blocklist():
    try:
        params = BlockListQuerySchema().load(request.args.to_dict())
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    user_id = get_jwt_identity()
    items, total = block_list_service.list_blocked(
        user_id,
        params["page"],
        params["per_page"],
        search=params["search"],
        risk_level=params["risk_level"],
        is_active=params["is_active"],
        sort_by=params["sort_by"],
        sort_dir=params["sort_dir"],
    )
    return jsonify(
        {
            "items": [item.to_dict() for item in items],
            "page": params["page"],
            "per_page": params["per_page"],
            "total": total,
            "total_pages": max(1, (total + params["per_page"] - 1) // params["per_page"]),
        }
    )


@protection_bp.post("/blocklist")
@limiter.limit("30 per minute")
@jwt_required()
def block_website():
    try:
        data = BlockWebsiteSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    user_id = get_jwt_identity()
    entry = block_list_service.block_website(
        user_id,
        data["target"],
        data["trust_score"],
        data["risk_level"],
        data["reasons"],
        scanner_type=data["scanner_type"],
        scan_id=data["scan_id"],
    )
    notification_service.create_notification(
        user_id=user_id,
        notif_type=NotificationType.WEBSITE_BLOCKED,
        title="Website blocked",
        message=f"{entry.domain} was added to your Personal Block List.",
    )
    audit_service.log_action(user_id, AuditAction.BLOCKLIST_ADD, request.remote_addr, domain=entry.domain)
    return jsonify({"message": "Website blocked.", "entry": entry.to_dict()}), 201


@protection_bp.delete("/blocklist/<int:entry_id>")
@limiter.limit("30 per minute")
@jwt_required()
def unblock_website(entry_id: int):
    user_id = get_jwt_identity()
    entry = block_list_service.unblock(user_id, entry_id)
    notification_service.create_notification(
        user_id=user_id,
        notif_type=NotificationType.WEBSITE_UNBLOCKED,
        title="Website unblocked",
        message=f"{entry.domain} was removed from your Personal Block List.",
    )
    audit_service.log_action(user_id, AuditAction.BLOCKLIST_REMOVE, request.remote_addr, domain=entry.domain)
    return jsonify({"message": "Website unblocked.", "entry": entry.to_dict()})


@protection_bp.post("/blocklist/<int:entry_id>/restore")
@limiter.limit("30 per minute")
@jwt_required()
def restore_website(entry_id: int):
    user_id = get_jwt_identity()
    entry = block_list_service.restore(user_id, entry_id)
    return jsonify({"message": "Website restored to your Personal Block List.", "entry": entry.to_dict()})


@protection_bp.get("/blocklist/export")
@jwt_required()
def export_blocklist():
    fmt = request.args.get("format", "json").lower()
    user_id = get_jwt_identity()

    if fmt == "csv":
        csv_text = block_list_service.export_csv(user_id)
        return Response(
            csv_text,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=cybershield-block-list.csv"},
        )
    if fmt == "json":
        return jsonify({"items": block_list_service.export_json(user_id)})

    raise APIError("Unsupported export format — use 'json' or 'csv'.", 422)


@protection_bp.get("/stats")
@jwt_required()
def get_protection_stats():
    return jsonify(protection_service.get_protection_stats(get_jwt_identity()))


@protection_bp.get("/community")
@jwt_required()
def get_community_intel():
    try:
        params = CommunityQuerySchema().load(request.args.to_dict())
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    domains = [d.strip().lower() for d in params["domains"].split(",") if d.strip()][:50]
    return jsonify({"items": community_intel_service.get_community_intel(domains)})


@protection_bp.get("/community/top")
@jwt_required()
def get_top_community_threats():
    return jsonify({"items": community_intel_service.list_top_community_threats()})


@protection_bp.post("/explain")
@jwt_required()
def explain_result():
    try:
        data = ExplainRequestSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    return jsonify(explanation_service.generate_explanation(data["risk"], data["trust_score"], data["reasons"], data["rules"]))


@protection_bp.post("/report")
@limiter.limit("15 per minute")
@jwt_required()
def report_website():
    try:
        data = ReportWebsiteSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    user_id = get_jwt_identity()
    domain = block_list_service.extract_hostname(data["target"])
    audit_service.log_action(
        user_id, AuditAction.WEBSITE_REPORTED, request.remote_addr, domain=domain, reasons=data["reasons"]
    )
    return jsonify({"message": f"Thanks — {domain} has been reported for admin review."}), 201


# --- Browser extension sync/enforcement ------------------------------------


@protection_bp.get("/sync")
@jwt_required()
def sync_for_extension():
    """Polled by the browser extension's background service worker (Phase 9)
    — a lightweight payload with just what enforcement needs, cached
    client-side rather than fetched on every navigation."""
    user_id = get_jwt_identity()
    settings = user_settings_service.get_or_create_settings(user_id)
    return jsonify(
        {
            "blocked_domains": block_list_service.get_active_entries_lite(user_id),
            "protection_mode": settings.protection_mode,
        }
    )


@protection_bp.post("/extension-blocked-event")
@limiter.limit("60 per minute")
@jwt_required()
def extension_blocked_event():
    """The extension calls this the moment it actually enforces a hard block
    on a page load — this is what makes "Extension Blocked Access" (Feature
    9) a real, server-recorded event rather than a client-only toast."""
    try:
        data = ExtensionBlockedEventSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    user_id = get_jwt_identity()
    notification_service.create_notification(
        user_id=user_id,
        notif_type=NotificationType.EXTENSION_BLOCKED_ACCESS,
        title="Extension blocked access",
        message=f"The CyberShield extension blocked access to {data['domain']}.",
    )
    audit_service.log_action(user_id, AuditAction.EXTENSION_EVENT, request.remote_addr, blocked_domain=data["domain"])
    return jsonify({"message": "Recorded."}), 201
