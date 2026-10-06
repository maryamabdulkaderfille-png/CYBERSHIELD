from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.extensions import limiter
from app.models.audit_log import AuditAction
from app.models.user_restriction import RestrictableFeature
from app.schemas.scan import ScanHistoryQuerySchema, ScanRequestSchema
from app.services import audit_service, community_intel_service, scan_service, user_restriction_service
from app.services.block_list_service import extract_hostname
from app.utils.client import detect_source
from app.utils.errors import APIError

scans_bp = Blueprint("scans", __name__)


@scans_bp.post("/scan")
@limiter.limit("20 per minute")
@user_restriction_service.require_not_restricted(RestrictableFeature.URL)
def scan_url_endpoint():
    try:
        data = ScanRequestSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    user_id = get_jwt_identity()
    source = detect_source(request)
    scan = scan_service.perform_and_store_scan(user_id, data["url"].strip(), source=source)
    if source == "extension":
        audit_service.log_action(user_id, AuditAction.EXTENSION_EVENT, request.remote_addr, scan_id=scan.id)
    if scan.risk_level == "Dangerous":
        community_intel_service.maybe_alert_user(user_id, extract_hostname(scan.url))
    return jsonify(scan.to_detail_dict()), 201


@scans_bp.get("/history")
@jwt_required()
def scan_history_endpoint():
    try:
        params = ScanHistoryQuerySchema().load(request.args.to_dict())
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    user_id = get_jwt_identity()
    items, total = scan_service.get_scan_history(
        user_id,
        page=params["page"],
        per_page=params["per_page"],
        search=params["search"],
        risk_level=params["risk_level"],
    )

    return jsonify(
        {
            "items": [scan.to_summary_dict() for scan in items],
            "page": params["page"],
            "per_page": params["per_page"],
            "total": total,
            "total_pages": max(1, (total + params["per_page"] - 1) // params["per_page"]),
        }
    )


@scans_bp.get("/history/<int:scan_id>")
@jwt_required()
def scan_detail_endpoint(scan_id: int):
    user_id = get_jwt_identity()
    scan = scan_service.get_scan_by_id(user_id, scan_id)
    if scan is None:
        raise APIError("Scan not found.", 404)
    return jsonify(scan.to_detail_dict())


@scans_bp.get("/stats")
@jwt_required()
def scan_stats_endpoint():
    user_id = get_jwt_identity()
    return jsonify(scan_service.get_dashboard_stats(user_id))
