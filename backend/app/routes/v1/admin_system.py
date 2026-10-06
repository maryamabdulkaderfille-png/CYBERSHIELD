from flask import Blueprint, jsonify

from app.rbac import require_permission
from app.services import system_monitoring_service

admin_system_bp = Blueprint("admin_system", __name__)


@admin_system_bp.get("/health")
@require_permission("system.monitor")
def get_system_health():
    return jsonify(system_monitoring_service.get_system_health())
