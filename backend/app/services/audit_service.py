"""Append-only audit trail (Phase 7). One writer function, called from the
existing route handlers that already know what happened — this module never
infers an action from a request, it just records what it's told."""

from app.extensions import db
from app.models.audit_log import AuditLog, AuditStatus


def log_action(
    user_id: str | None,
    action: str,
    ip_address: str | None = None,
    status: str = AuditStatus.SUCCESS,
    **details,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        status=status,
        ip_address=ip_address,
        details=details or None,
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def count_actions(user_id: str, action: str, since) -> int:
    """How many times this user triggered `action` since a given timestamp —
    used for abuse guards (e.g. capping /auth/resend-verification) that need
    a durable count independent of any other table's row lifecycle."""
    return AuditLog.query.filter(
        AuditLog.user_id == user_id, AuditLog.action == action, AuditLog.created_at >= since
    ).count()


def list_audit_logs(
    page: int,
    per_page: int,
    action: str | None = None,
    user_id: str | None = None,
    status: str | None = None,
    search: str | None = None,
    date_from=None,
    date_to=None,
) -> tuple[list[AuditLog], int]:
    query = AuditLog.query

    if action:
        query = query.filter_by(action=action)
    if user_id:
        query = query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(AuditLog.ip_address.ilike(f"%{search}%"))
    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)
    if date_to:
        query = query.filter(AuditLog.created_at <= date_to)

    query = query.order_by(AuditLog.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total
