"""Admin-only platform stats (System Overview + Threat Intelligence combined
into one payload) — composes the two existing services rather than
duplicating their logic. `/threats` itself stays available to any
authenticated user (see routes/v1/threats.py); this route exists for admin
tooling that wants both in a single, permission-gated call."""

from flask import Blueprint, jsonify

from app.rbac import require_permission
from app.services import admin_dashboard_service, session_service, threat_intel_service

admin_stats_bp = Blueprint("admin_stats", __name__)


@admin_stats_bp.get("")
@require_permission("system.monitor")
def get_platform_stats():
    return jsonify(
        {
            "overview": admin_dashboard_service.get_system_overview(),
            "threat_intelligence": threat_intel_service.get_threat_intelligence_summary(),
            "active_users": {
                "count": session_service.count_active_users(),
                "window_minutes": session_service.ACTIVE_SESSION_WINDOW_MINUTES,
            },
        }
    )
