"""Browser Extension support (Phase 6).

Deliberately minimal: the extension's default behavior is to call the
existing, unchanged `/url/scan` endpoint (the same one the web dashboard
uses) so automatic page-visit scans show up in the user's real scan
history/dashboard exactly like a manual scan would. The one new route here
exists only for the extension's Privacy Mode, where the user has opted out
of having every page they visit logged against their account — it reuses
the exact same detection engine (`scan_service.perform_ephemeral_scan`,
which calls the same `url_scanner.engine.scan_url` the persisting path
calls) without writing anything to the database.
"""

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.extensions import limiter
from app.models.user_restriction import RestrictableFeature
from app.schemas.scan import ScanRequestSchema
from app.services import scan_service, user_restriction_service

extension_bp = Blueprint("extension", __name__)


@extension_bp.post("/scan")
@limiter.limit("20 per minute")
@user_restriction_service.require_not_restricted(RestrictableFeature.URL)
def ephemeral_scan_endpoint():
    try:
        data = ScanRequestSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    # Deliberately NOT audit-logged: Privacy Mode's whole point (see the
    # extension options page copy) is that "nothing is logged anywhere on
    # this device or the server" — an audit-log row here would quietly
    # break that promise. Non-privacy-mode extension scans (the default)
    # go through /url/scan instead and ARE audited there (source="extension").
    result = scan_service.perform_ephemeral_scan(data["url"].strip())
    return jsonify(result), 200
