"""Weekly in-app security summary — backs the Settings page's "Weekly
security summary" toggle. Triggered either by the dev-only APScheduler job
(see app/scheduler.py) or manually/production via `flask send-weekly-summaries`,
meant to be wired to an external cron since gunicorn's multiple worker
processes make an in-process scheduler unsafe there (it would fire once per
worker). Counts are read from the same three scan tables as the rest of the
dashboard — nothing here re-implements detection logic.
"""

from datetime import timedelta

from app.constants import RiskLevel
from app.extensions import db
from app.models.email_scan import EmailScanHistory
from app.models.notification import Notification, NotificationType
from app.models.qr_scan import QRScanHistory
from app.models.scan import ScanHistory
from app.models.user import User, UserStatus
from app.models.user_settings import UserSettings
from app.services import notification_service
from app.utils.time import utcnow

_SCAN_MODELS = (ScanHistory, EmailScanHistory, QRScanHistory)
_SUMMARY_WINDOW_DAYS = 7
# Guards against a duplicate summary if the job runs more than once in the
# same week (e.g. a manual CLI run shortly after the scheduled one).
_MIN_GAP_DAYS = 6


def _counts_for_user(user_id: str, since) -> tuple[int, int, int]:
    total = dangerous = suspicious = 0
    for model in _SCAN_MODELS:
        rows = (
            model.query.filter(model.user_id == user_id, model.scan_date >= since)
            .with_entities(model.risk_level)
            .all()
        )
        for (risk_level,) in rows:
            total += 1
            if risk_level == RiskLevel.DANGEROUS:
                dangerous += 1
            elif risk_level == RiskLevel.SUSPICIOUS:
                suspicious += 1
    return total, dangerous, suspicious


def _already_sent_recently(user_id: str, since) -> bool:
    return (
        Notification.query.filter(
            Notification.user_id == user_id,
            Notification.type == NotificationType.WEEKLY_SUMMARY,
            Notification.created_at >= since,
        ).first()
        is not None
    )


def _eligible_user_ids() -> list[str]:
    # UserSettings rows are created lazily on first Settings-page visit (see
    # user_settings_service.get_or_create_settings), so a plain inner join
    # would silently skip every user who's never opened Settings — an outer
    # join treats a missing row as the column's default (True), matching
    # what that user would actually see if they opened the page.
    rows = (
        db.session.query(User.id)
        .outerjoin(UserSettings, UserSettings.user_id == User.id)
        .filter(
            User.status == UserStatus.ACTIVE,
            db.or_(UserSettings.user_id.is_(None), UserSettings.notify_weekly_summary.is_(True)),
        )
        .all()
    )
    return [row[0] for row in rows]


def generate_weekly_summaries() -> int:
    """Creates one weekly-summary notification per eligible user. Returns how
    many were created."""
    since = utcnow() - timedelta(days=_SUMMARY_WINDOW_DAYS)
    recent_cutoff = utcnow() - timedelta(days=_MIN_GAP_DAYS)

    created = 0
    for user_id in _eligible_user_ids():
        if _already_sent_recently(user_id, recent_cutoff):
            continue

        total, dangerous, suspicious = _counts_for_user(user_id, since)
        notification_service.create_notification(
            user_id=user_id,
            notif_type=NotificationType.WEEKLY_SUMMARY,
            title="Weekly Security Summary",
            message=(
                f"This week: {total} scan{'s' if total != 1 else ''} · "
                f"{dangerous} flagged Dangerous · {suspicious} Suspicious."
            ),
        )
        created += 1
    return created
