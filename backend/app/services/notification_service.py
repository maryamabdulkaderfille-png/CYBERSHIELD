"""Notification creation and management.

`notify_scan_result` is the single hook called from the three existing scan
services (url/email/qr) after a scan is persisted — it decides whether the
result warrants a notification and creates one if so. The scan services
themselves don't know anything about notification rules; this keeps that
policy in one place instead of duplicated across three call sites.
"""

from app.constants import RiskLevel
from app.extensions import db
from app.models.notification import Notification, NotificationType
from app.services import user_settings_service

RECENT_LIMIT_DEFAULT = 20

_SCAN_NOTIFICATION_RULES = {
    # scanner_type -> (risk levels that warrant a notification, type, title builder, message builder, settings field)
    "url": (
        {RiskLevel.DANGEROUS},
        NotificationType.HIGH_RISK_URL,
        "High Risk URL Detected",
        lambda target: f"The URL {target} was scanned and classified as Dangerous.",
        "notify_high_risk_url",
    ),
    "email": (
        {RiskLevel.DANGEROUS},
        NotificationType.DANGEROUS_EMAIL,
        "Dangerous Email Detected",
        lambda target: f"An email from {target} was scanned and classified as Dangerous.",
        "notify_dangerous_email",
    ),
    "qr": (
        {RiskLevel.SUSPICIOUS, RiskLevel.DANGEROUS},
        NotificationType.QR_THREAT,
        "QR Code Threat Detected",
        lambda target: f"A scanned QR code ({target}) was classified as suspicious or dangerous.",
        "notify_qr_threat",
    ),
}


def notify_scan_result(user_id: str, scanner_type: str, risk_level: str, target: str, scan_id: int) -> None:
    rule = _SCAN_NOTIFICATION_RULES.get(scanner_type)
    if rule is None:
        return

    trigger_levels, notif_type, title, message_builder, settings_field = rule
    if risk_level not in trigger_levels:
        return

    settings = user_settings_service.get_or_create_settings(user_id)
    if not getattr(settings, settings_field):
        return

    create_notification(
        user_id=user_id,
        notif_type=notif_type,
        title=title,
        message=message_builder(target),
        scanner_type=scanner_type,
        scan_id=scan_id,
    )


def create_notification(
    user_id: str,
    notif_type: str,
    title: str,
    message: str,
    scanner_type: str | None = None,
    scan_id: int | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=notif_type,
        title=title,
        message=message,
        scanner_type=scanner_type,
        scan_id=scan_id,
    )
    db.session.add(notification)
    db.session.commit()
    return notification


def list_notifications(
    user_id: str, page: int, per_page: int, unread_only: bool = False
) -> tuple[list[Notification], int]:
    query = Notification.query.filter_by(user_id=user_id)
    if unread_only:
        query = query.filter_by(is_read=False)
    query = query.order_by(Notification.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total


def get_unread_count(user_id: str) -> int:
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()


def mark_read(user_id: str, notification_id: int) -> Notification | None:
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if notification is None:
        return None
    notification.is_read = True
    db.session.commit()
    return notification


def mark_all_read(user_id: str) -> int:
    updated = Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    db.session.commit()
    return updated


def delete_notification(user_id: str, notification_id: int) -> bool:
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if notification is None:
        return False
    db.session.delete(notification)
    db.session.commit()
    return True
