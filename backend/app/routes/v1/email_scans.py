from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.extensions import limiter
from app.models.user_restriction import RestrictableFeature
from app.schemas.email_scan import validate_email_text, validate_email_upload
from app.schemas.scan import ScanHistoryQuerySchema
from app.services import email_scan_service, user_restriction_service
from app.services.email_scanner.msg_parser import parse_msg_file
from app.utils.errors import APIError

email_scans_bp = Blueprint("email_scans", __name__)


@email_scans_bp.post("/scan")
@limiter.limit("15 per minute")
@user_restriction_service.require_not_restricted(RestrictableFeature.EMAIL)
def scan_email_endpoint():
    email_text = (request.form.get("email_text") or "").strip()
    uploaded_file = request.files.get("email_file")

    if email_text and uploaded_file:
        raise APIError("Provide either pasted email content or a file upload, not both.", 422)
    if not email_text and not uploaded_file:
        raise APIError("Provide either pasted email content or a file upload.", 422)

    user_id = get_jwt_identity()

    if uploaded_file:
        content = uploaded_file.read()
        ext = validate_email_upload(uploaded_file.filename, content)
        if ext == ".msg":
            parse_msg_file(content)  # always raises a clean 422 today — see msg_parser docstring
        scan = email_scan_service.perform_and_store_email_scan(user_id, content)
    else:
        validated_text = validate_email_text(email_text)
        scan = email_scan_service.perform_and_store_email_scan(user_id, validated_text)

    return jsonify(scan.to_detail_dict()), 201


@email_scans_bp.get("/history")
@jwt_required()
def email_scan_history_endpoint():
    try:
        params = ScanHistoryQuerySchema().load(request.args.to_dict())
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    user_id = get_jwt_identity()
    items, total = email_scan_service.get_email_scan_history(
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


@email_scans_bp.get("/history/<int:scan_id>")
@jwt_required()
def email_scan_detail_endpoint(scan_id: int):
    user_id = get_jwt_identity()
    scan = email_scan_service.get_email_scan_by_id(user_id, scan_id)
    if scan is None:
        raise APIError("Email scan not found.", 404)
    return jsonify(scan.to_detail_dict())


@email_scans_bp.get("/stats")
@jwt_required()
def email_scan_stats_endpoint():
    user_id = get_jwt_identity()
    return jsonify(email_scan_service.get_email_dashboard_stats(user_id))
