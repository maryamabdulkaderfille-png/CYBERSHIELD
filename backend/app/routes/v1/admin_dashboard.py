from flask import Blueprint, jsonify

from app.rbac import require_permission
from app.services import admin_dashboard_service

admin_dashboard_bp = Blueprint("admin_dashboard", __name__)


@admin_dashboard_bp.get("")
@require_permission("system.monitor")
def get_overview():
    return jsonify(admin_dashboard_service.get_system_overview())
