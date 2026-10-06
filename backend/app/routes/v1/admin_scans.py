"""Admin Scan Management (Phase 7) — the exact same unified_scan_service
that powers the per-user Scan Center, just called with user_id=None for a
platform-wide view. No parallel query logic."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError

from app.extensions import limiter
from app.models.audit_log import AuditAction
from app.rbac import require_permission
from app.schemas.unified_scan import BulkDeleteSchema, UnifiedScanQuerySchema
from app.services import audit_service, unified_scan_service
from app.services.unified_scan_service import UnifiedScanFilters
from app.utils.errors import APIError

admin_scans_bp = Blueprint("admin_scans", __name__)


@admin_scans_bp.get("")
@require_permission("scans.view")
def list_all_scans():
    try:
        params = UnifiedScanQuerySchema().load(request.args.to_dict())
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

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
    items, total = unified_scan_service.get_unified_scans(None, params["page"], params["per_page"], filters)

    return jsonify(
        {
            "items": items,
            "page": params["page"],
            "per_page": params["per_page"],
            "total": total,
            "total_pages": max(1, (total + params["per_page"] - 1) // params["per_page"]),
        }
    )


@admin_scans_bp.get("/stats")
@require_permission("scans.view")
def platform_scan_stats():
    return jsonify(unified_scan_service.get_unified_stats(None))


@admin_scans_bp.get("/<scanner_type>/<int:scan_id>")
@require_permission("scans.view")
def get_scan_detail(scanner_type: str, scan_id: int):
    record = unified_scan_service.get_scan_record(None, scanner_type, scan_id)
    if record is None:
        raise APIError("Scan not found.", 404)
    return jsonify(record.to_detail_dict())


@admin_scans_bp.delete("/<scanner_type>/<int:scan_id>")
@limiter.limit("30 per minute")
@require_permission("scans.manage")
def delete_scan(scanner_type: str, scan_id: int):
    deleted = unified_scan_service.delete_scan(None, scanner_type, scan_id)
    if not deleted:
        raise APIError("Scan not found.", 404)
    audit_service.log_action(
        get_jwt_identity(), AuditAction.SCAN_DELETED, request.remote_addr,
        scanner_type=scanner_type, scan_id=scan_id, admin_action=True,
    )
    return jsonify({"message": "Scan deleted."})


@admin_scans_bp.post("/bulk-delete")
@limiter.limit("15 per minute")
@require_permission("scans.manage")
def bulk_delete_scans():
    try:
        data = BulkDeleteSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    deleted_count = unified_scan_service.bulk_delete_scans(None, data["items"])
    if deleted_count:
        audit_service.log_action(
            get_jwt_identity(), AuditAction.SCAN_DELETED, request.remote_addr,
            deleted_count=deleted_count, admin_action=True,
        )
    return jsonify({"message": f"{deleted_count} scan(s) deleted.", "deleted_count": deleted_count})


@admin_scans_bp.get("/export")
@require_permission("scans.view")
def export_scans():
    raise APIError("Scan export is not yet implemented in this version of CyberShield.", 501)
