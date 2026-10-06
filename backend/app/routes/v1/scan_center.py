from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.models.audit_log import AuditAction
from app.schemas.unified_scan import BulkDeleteSchema, RangeQuerySchema, UnifiedScanQuerySchema
from app.services import audit_service, unified_scan_service
from app.services.unified_scan_service import UnifiedScanFilters
from app.utils.errors import APIError

scan_center_bp = Blueprint("scan_center", __name__)


@scan_center_bp.get("")
@jwt_required()
def list_unified_scans():
    try:
        params = UnifiedScanQuerySchema().load(request.args.to_dict())
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    user_id = get_jwt_identity()
    filters = UnifiedScanFilters(
        scanner_type=params["scanner_type"],
        risk_level=params["risk_level"],
        search=params["search"],
        trust_score_min=params["trust_score_min"],
        trust_score_max=params["trust_score_max"],
        date_from=params["date_from"],
        date_to=params["date_to"],
        source=params["source"],
        sort_by=params["sort_by"],
        sort_dir=params["sort_dir"],
    )
    items, total = unified_scan_service.get_unified_scans(user_id, params["page"], params["per_page"], filters)

    return jsonify(
        {
            "items": items,
            "page": params["page"],
            "per_page": params["per_page"],
            "total": total,
            "total_pages": max(1, (total + params["per_page"] - 1) // params["per_page"]),
        }
    )


@scan_center_bp.get("/stats")
@jwt_required()
def unified_scan_stats():
    user_id = get_jwt_identity()
    return jsonify(unified_scan_service.get_unified_stats(user_id))


@scan_center_bp.get("/stats/range")
@jwt_required()
def unified_scan_stats_range():
    try:
        params = RangeQuerySchema().load(request.args.to_dict())
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    user_id = get_jwt_identity()
    return jsonify(unified_scan_service.get_unified_stats_range(user_id, params["range"]))


@scan_center_bp.get("/stats/trend")
@jwt_required()
def unified_scan_stats_trend():
    user_id = get_jwt_identity()
    return jsonify(unified_scan_service.get_unified_stats_trend(user_id))


@scan_center_bp.get("/<scanner_type>/<int:scan_id>")
@jwt_required()
def get_unified_scan_detail(scanner_type: str, scan_id: int):
    user_id = get_jwt_identity()
    record = unified_scan_service.get_scan_record(user_id, scanner_type, scan_id)
    if record is None:
        raise APIError("Scan not found.", 404)
    return jsonify(record.to_detail_dict())


@scan_center_bp.delete("/<scanner_type>/<int:scan_id>")
@jwt_required()
def delete_unified_scan(scanner_type: str, scan_id: int):
    user_id = get_jwt_identity()
    deleted = unified_scan_service.delete_scan(user_id, scanner_type, scan_id)
    if not deleted:
        raise APIError("Scan not found.", 404)
    audit_service.log_action(
        user_id, AuditAction.SCAN_DELETED, request.remote_addr, scanner_type=scanner_type, scan_id=scan_id
    )
    return jsonify({"message": "Scan deleted."})


@scan_center_bp.post("/bulk-delete")
@jwt_required()
def bulk_delete_unified_scans():
    try:
        data = BulkDeleteSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    user_id = get_jwt_identity()
    deleted_count = unified_scan_service.bulk_delete_scans(user_id, data["items"])
    if deleted_count:
        audit_service.log_action(user_id, AuditAction.SCAN_DELETED, request.remote_addr, deleted_count=deleted_count)
    return jsonify({"message": f"{deleted_count} scan(s) deleted.", "deleted_count": deleted_count})
