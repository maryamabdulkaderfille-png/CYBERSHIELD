from flask import Blueprint, jsonify, request, Response
from flask_jwt_extended import get_jwt_identity

from app.extensions import db
from app.models.audit_log import AuditAction
from app.models.user import User
from app.models.user_restriction import RestrictableFeature
from app.services import audit_service, report_service, user_restriction_service
from app.services.report_export_service import get_exporter
from app.services.unified_scan_service import SCANNER_TYPES
from app.utils.errors import APIError

reports_bp = Blueprint("reports", __name__)


def _current_user() -> User:
    user = db.session.get(User, get_jwt_identity())
    if user is None:
        raise APIError("User not found.", 404)
    return user


@reports_bp.get("/<scanner_type>/<int:scan_id>")
@user_restriction_service.require_not_restricted(RestrictableFeature.REPORTS)
def get_report(scanner_type: str, scan_id: int):
    if scanner_type not in SCANNER_TYPES:
        raise APIError(f"Unknown scanner type: {scanner_type}", 422)

    user = _current_user()
    report = report_service.build_report(user, scanner_type, scan_id)
    audit_service.log_action(
        user.id, AuditAction.REPORT_GENERATED, request.remote_addr, scanner_type=scanner_type, scan_id=scan_id
    )
    return jsonify(report)


@reports_bp.post("/<scanner_type>/<int:scan_id>/export")
@user_restriction_service.require_not_restricted(RestrictableFeature.REPORTS)
def export_report(scanner_type: str, scan_id: int):
    if scanner_type not in SCANNER_TYPES:
        raise APIError(f"Unknown scanner type: {scanner_type}", 422)

    export_format = (request.get_json(silent=True) or {}).get("format", "pdf")
    report = report_service.build_report(_current_user(), scanner_type, scan_id)

    exporter = get_exporter(export_format)
    content = exporter.export(report)
    filename = f"cybershield-report-{scanner_type}-{scan_id}.pdf"
    response = Response(content, mimetype="application/pdf")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response
