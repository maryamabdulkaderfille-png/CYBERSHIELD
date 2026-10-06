"""Community Intelligence (Phase 9, Feature 8) — aggregates ONLY CyberShield's
own BlockedWebsite data across every user; no external threat-intel API is
called (consistent with `threat_intel_service.InternalThreatFeedProvider`'s
same "our own data only" scope from Phase 5).

`confidence_percent` is an explicitly documented heuristic (not a statistical
guarantee): more independent users blocking the same domain is treated as
stronger signal, capped at 100%. It is derived, not fabricated — every input
is a real row in the database.
"""

from sqlalchemy import func

from app.extensions import db
from app.models.blocked_website import BlockedWebsite
from app.models.notification import Notification, NotificationType
from app.services import notification_service

CONFIDENCE_PER_REPORTER = 20
MAX_CONFIDENCE = 100
COMMUNITY_ALERT_THRESHOLD = 3


def _to_intel_dict(domain: str, blocked_by: int, first_seen, last_activity) -> dict:
    return {
        "domain": domain,
        "blocked_by_users": blocked_by,
        "confidence_percent": min(MAX_CONFIDENCE, blocked_by * CONFIDENCE_PER_REPORTER),
        "first_seen": f"{first_seen.isoformat()}Z" if first_seen else None,
        "recent_activity": f"{last_activity.isoformat()}Z" if last_activity else None,
    }


def get_community_intel(domains: list[str]) -> dict[str, dict]:
    """Bulk lookup — one query for however many domains the caller (e.g. the
    Blocked Websites page rendering a page of rows) needs enriched at once."""
    if not domains:
        return {}

    rows = (
        db.session.query(
            BlockedWebsite.domain,
            func.count(func.distinct(BlockedWebsite.user_id)),
            func.min(BlockedWebsite.blocked_at),
            func.max(BlockedWebsite.blocked_at),
        )
        .filter(BlockedWebsite.domain.in_(domains))
        .group_by(BlockedWebsite.domain)
        .all()
    )
    return {domain: _to_intel_dict(domain, count, first_seen, last_activity) for domain, count, first_seen, last_activity in rows}


def maybe_alert_user(user_id: str, domain: str) -> None:
    """Called after a Dangerous scan (see routes/v1/scans.py) — if enough
    *other* CyberShield users have already blocked this same domain, let
    this user know. De-duplicated per (user, domain) by checking for an
    already-sent alert first, so revisiting/rescanning the same dangerous
    domain doesn't spam a notification every time."""
    blocked_by = (
        db.session.query(func.count(func.distinct(BlockedWebsite.user_id)))
        .filter(BlockedWebsite.domain == domain, BlockedWebsite.user_id != user_id)
        .scalar()
        or 0
    )
    if blocked_by < COMMUNITY_ALERT_THRESHOLD:
        return

    already_alerted = Notification.query.filter(
        Notification.user_id == user_id,
        Notification.type == NotificationType.COMMUNITY_THREAT_ALERT,
        Notification.message.like(f"%{domain}%"),
    ).first()
    if already_alerted is not None:
        return

    notification_service.create_notification(
        user_id=user_id,
        notif_type=NotificationType.COMMUNITY_THREAT_ALERT,
        title="Community threat alert",
        message=f"{domain} has already been blocked by {blocked_by} other CyberShield user(s).",
    )


def list_top_community_threats(limit: int = 10) -> list[dict]:
    rows = (
        db.session.query(
            BlockedWebsite.domain,
            func.count(func.distinct(BlockedWebsite.user_id)).label("blocked_by"),
            func.min(BlockedWebsite.blocked_at).label("first_seen"),
            func.max(BlockedWebsite.blocked_at).label("last_activity"),
        )
        .group_by(BlockedWebsite.domain)
        .order_by(func.count(func.distinct(BlockedWebsite.user_id)).desc())
        .limit(limit)
        .all()
    )
    return [_to_intel_dict(r.domain, r.blocked_by, r.first_seen, r.last_activity) for r in rows]
