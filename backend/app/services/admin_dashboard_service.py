"""Admin System Overview (Phase 7) — every number here is computed from
existing tables via existing/generalized services (unified_scan_service,
audit_service, system_monitoring_service); nothing is a second copy of
logic those modules already own."""

from app.models.audit_log import AuditAction
from app.models.notification import Notification
from app.models.scan import ScanHistory
from app.models.user import User
from app.services import audit_service, system_monitoring_service, unified_scan_service
from app.utils.cache import cacheable


@cacheable(ttl_seconds=60)
def get_system_overview() -> dict:
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    verified_users = User.query.filter_by(is_verified=True).count()
    admin_users = User.query.filter_by(role="admin").count()

    unified_stats = unified_scan_service.get_unified_stats(None)

    extension_scans_today = ScanHistory.query.filter_by(source="extension").count()

    notifications_sent = Notification.query.count()

    recent_logins, _ = audit_service.list_audit_logs(page=1, per_page=10, action=AuditAction.LOGIN)

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users,
            "verified": verified_users,
            "admins": admin_users,
        },
        "scans": unified_stats,
        "extension_activity": {"scans_recorded": extension_scans_today},
        "notifications_sent": notifications_sent,
        "recent_logins": [log.to_dict() for log in recent_logins],
        "system_health": system_monitoring_service.get_system_health(),
    }
