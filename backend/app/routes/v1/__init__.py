from flask import Blueprint

from app.routes.v1.admin_audit import admin_audit_bp
from app.routes.v1.admin_blacklist import admin_blacklist_bp
from app.routes.v1.admin_dashboard import admin_dashboard_bp
from app.routes.v1.admin_rules import admin_rules_bp
from app.routes.v1.admin_scans import admin_scans_bp
from app.routes.v1.admin_stats import admin_stats_bp
from app.routes.v1.admin_system import admin_system_bp
from app.routes.v1.admin_users import admin_users_bp
from app.routes.v1.auth import auth_bp
from app.routes.v1.dashboard import dashboard_bp
from app.routes.v1.email_scans import email_scans_bp
from app.routes.v1.extension import extension_bp
from app.routes.v1.guest import guest_bp
from app.routes.v1.notifications import notifications_bp
from app.routes.v1.profile import profile_bp
from app.routes.v1.protection import protection_bp
from app.routes.v1.qr_scans import qr_scans_bp
from app.routes.v1.reports import reports_bp
from app.routes.v1.scan_center import scan_center_bp
from app.routes.v1.scans import scans_bp
from app.routes.v1.settings import settings_bp
from app.routes.v1.threats import threats_bp
from app.routes.v1.users import users_bp

api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")
api_v1_bp.register_blueprint(auth_bp, url_prefix="/auth")
api_v1_bp.register_blueprint(users_bp, url_prefix="/users")
api_v1_bp.register_blueprint(scans_bp, url_prefix="/url")
api_v1_bp.register_blueprint(email_scans_bp, url_prefix="/email")
api_v1_bp.register_blueprint(qr_scans_bp, url_prefix="/qr")
api_v1_bp.register_blueprint(scan_center_bp, url_prefix="/scans")
api_v1_bp.register_blueprint(reports_bp, url_prefix="/reports")
api_v1_bp.register_blueprint(dashboard_bp, url_prefix="/dashboard")
api_v1_bp.register_blueprint(profile_bp, url_prefix="/profile")
api_v1_bp.register_blueprint(settings_bp, url_prefix="/settings")
api_v1_bp.register_blueprint(notifications_bp, url_prefix="/notifications")
api_v1_bp.register_blueprint(threats_bp, url_prefix="/threats")
api_v1_bp.register_blueprint(extension_bp, url_prefix="/extension")
api_v1_bp.register_blueprint(guest_bp, url_prefix="/guest")
api_v1_bp.register_blueprint(admin_dashboard_bp, url_prefix="/admin/dashboard")
api_v1_bp.register_blueprint(admin_users_bp, url_prefix="/admin/users")
api_v1_bp.register_blueprint(admin_scans_bp, url_prefix="/admin/scans")
api_v1_bp.register_blueprint(admin_blacklist_bp, url_prefix="/admin/blacklist")
api_v1_bp.register_blueprint(admin_rules_bp, url_prefix="/admin/rules")
api_v1_bp.register_blueprint(admin_audit_bp, url_prefix="/admin/audit-logs")
api_v1_bp.register_blueprint(admin_system_bp, url_prefix="/admin/system")
api_v1_bp.register_blueprint(admin_stats_bp, url_prefix="/admin/stats")
api_v1_bp.register_blueprint(protection_bp, url_prefix="/protection")
