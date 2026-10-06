from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.extensions import limiter
from app.models.user_restriction import RestrictableFeature
from app.schemas.qr_scan import validate_qr_upload
from app.schemas.scan import ScanHistoryQuerySchema
from app.services import qr_scan_service, user_restriction_service
from app.services.qr_scanner.decoder import InvalidImageError, NoQRCodeFoundError
from app.utils.errors import APIError

qr_scans_bp = Blueprint("qr_scans", __name__)


@qr_scans_bp.post("/scan")
@limiter.limit("15 per minute")
@user_restriction_service.require_not_restricted(RestrictableFeature.QR)
def scan_qr_endpoint():
    uploaded_file = request.files.get("qr_image")
    if not uploaded_file:
        raise APIError("An image file is required.", 422)

    content = uploaded_file.read()
    validate_qr_upload(uploaded_file.filename, content)

    user_id = get_jwt_identity()
    try:
        scan = qr_scan_service.perform_and_store_qr_scan(user_id, content)
    except InvalidImageError as exc:
        raise APIError(str(exc), 422) from exc
    except NoQRCodeFoundError as exc:
        raise APIError(str(exc), 422) from exc

    return jsonify(scan.to_detail_dict()), 201


@qr_scans_bp.get("/history")
@jwt_required()
def qr_scan_history_endpoint():
    try:
        params = ScanHistoryQuerySchema().load(request.args.to_dict())
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    user_id = get_jwt_identity()
    items, total = qr_scan_service.get_qr_scan_history(
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


@qr_scans_bp.get("/history/<int:scan_id>")
@jwt_required()
def qr_scan_detail_endpoint(scan_id: int):
    user_id = get_jwt_identity()
    scan = qr_scan_service.get_qr_scan_by_id(user_id, scan_id)
    if scan is None:
        raise APIError("QR scan not found.", 404)
    return jsonify(scan.to_detail_dict())


@qr_scans_bp.get("/stats")
@jwt_required()
def qr_scan_stats_endpoint():
    user_id = get_jwt_identity()
    return jsonify(qr_scan_service.get_qr_dashboard_stats(user_id))
