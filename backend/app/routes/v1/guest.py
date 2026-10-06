"""Guest / Quick Scan — public, unauthenticated access to the three
scanners (Phase: Guest Quick Scan).

Deliberately thin: every route here calls the exact same ephemeral-scan
service functions used elsewhere for non-persisting scans
(`scan_service.perform_ephemeral_scan` already existed for the browser
extension's Privacy Mode; `email_scan_service.perform_ephemeral_email_scan`
and `qr_scan_service.perform_ephemeral_qr_scan` were added alongside this
file following that exact pattern). Same detection engine, same scoring,
same risk thresholds, same threat-intelligence pipeline as the authenticated
routes — nothing here re-implements or duplicates any analysis logic.

No `@jwt_required()` / no `user_restriction_service.require_not_restricted()`
on purpose — there is no account to restrict. Each route is instead
rate-limited per-IP (stricter than the authenticated equivalents, since an
anonymous caller has no account-level throttling to fall back on), and
returns only the scan result — no user data, no history, no admin data.
"""

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.extensions import limiter
from app.schemas.email_scan import validate_email_text, validate_email_upload
from app.schemas.qr_scan import validate_qr_upload
from app.schemas.scan import ScanRequestSchema
from app.services import email_scan_service, qr_scan_service, scan_service
from app.services.email_scanner.msg_parser import parse_msg_file
from app.services.qr_scanner.decoder import InvalidImageError, NoQRCodeFoundError
from app.utils.errors import APIError

guest_bp = Blueprint("guest", __name__)

GUEST_RATE_LIMIT = "10 per minute"


@guest_bp.post("/url/scan")
@limiter.limit(GUEST_RATE_LIMIT)
def guest_url_scan_endpoint():
    try:
        data = ScanRequestSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    result = scan_service.perform_ephemeral_scan(data["url"].strip())
    return jsonify(result), 200


@guest_bp.post("/email/scan")
@limiter.limit(GUEST_RATE_LIMIT)
def guest_email_scan_endpoint():
    email_text = (request.form.get("email_text") or "").strip()
    uploaded_file = request.files.get("email_file")

    if email_text and uploaded_file:
        raise APIError("Provide either pasted email content or a file upload, not both.", 422)
    if not email_text and not uploaded_file:
        raise APIError("Provide either pasted email content or a file upload.", 422)

    if uploaded_file:
        content = uploaded_file.read()
        ext = validate_email_upload(uploaded_file.filename, content)
        if ext == ".msg":
            parse_msg_file(content)  # always raises a clean 422 today — see msg_parser docstring
        result = email_scan_service.perform_ephemeral_email_scan(content)
    else:
        validated_text = validate_email_text(email_text)
        result = email_scan_service.perform_ephemeral_email_scan(validated_text)

    return jsonify(result), 200


@guest_bp.post("/qr/scan")
@limiter.limit(GUEST_RATE_LIMIT)
def guest_qr_scan_endpoint():
    uploaded_file = request.files.get("qr_image")
    if not uploaded_file:
        raise APIError("An image file is required.", 422)

    content = uploaded_file.read()
    validate_qr_upload(uploaded_file.filename, content)

    try:
        result = qr_scan_service.perform_ephemeral_qr_scan(content)
    except InvalidImageError as exc:
        raise APIError(str(exc), 422) from exc
    except NoQRCodeFoundError as exc:
        raise APIError(str(exc), 422) from exc

    return jsonify(result), 200
