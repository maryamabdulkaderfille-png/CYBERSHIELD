"""Protection Statistics (Phase 9 dashboard widget) — purely additive
aggregation over BlockedWebsite, kept in its own service/endpoint rather than
folded into dashboard_service.py so the existing `/dashboard` payload and its
widgets are never touched."""

from datetime import timedelta

from app.models.blocked_website import BlockedWebsite
from app.utils.time import utcnow

RECENT_LIMIT = 5


def get_protection_stats(user_id: str) -> dict:
    now = utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())

    base = BlockedWebsite.query.filter_by(user_id=user_id, is_active=True)
    blocked_today = base.filter(BlockedWebsite.blocked_at >= today_start).count()
    blocked_this_week = base.filter(BlockedWebsite.blocked_at >= week_start).count()
    total_blocked = base.count()
    recent = base.order_by(BlockedWebsite.blocked_at.desc()).limit(RECENT_LIMIT).all()

    return {
        "blocked_today": blocked_today,
        "blocked_this_week": blocked_this_week,
        "total_blocked_domains": total_blocked,
        "recent_blocked": [entry.to_dict() for entry in recent],
    }
