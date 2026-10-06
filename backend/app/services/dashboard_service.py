"""Advanced dashboard widgets (Phase 5).

Every widget here is computed from the three existing scan tables (or the
existing unified_scan_service aggregate) — nothing is fabricated. Time-series
bucketing (weekday, calendar day) is done in Python rather than pushed down
as dialect-specific SQL (SQLite's strftime vs. Postgres's date_trunc/extract
would otherwise have to be branched), trading a small amount of query
efficiency for portability — acceptable since every query here is already
bounded (a date range or a row-count limit), never a full table scan.
"""

from collections import defaultdict
from datetime import timedelta

from sqlalchemy import func

from app.constants import RiskLevel
from app.extensions import db
from app.models.email_scan import EmailScanHistory
from app.models.qr_scan import QRScanHistory
from app.models.scan import ScanHistory
from app.services import notification_service, scan_analytics, unified_scan_service
from app.utils.time import utcnow

_SCAN_MODELS = (ScanHistory, EmailScanHistory, QRScanHistory)


def _rows_since(user_id: str | None, since):
    """(scan_date, risk_level) tuples across all three scan tables, bounded
    to a time window — used for trend/activity/heatmap bucketing.
    `user_id=None` scans platform-wide, for threat_intel_service's reuse."""
    rows = []
    for model in _SCAN_MODELS:
        query = model.query.filter(model.scan_date >= since)
        if user_id is not None:
            query = query.filter(model.user_id == user_id)
        rows.extend(query.with_entities(model.scan_date, model.risk_level).all())
    return rows


def daily_buckets(user_id: str | None, days: int, only_threats: bool) -> list[dict]:
    since = utcnow() - timedelta(days=days)
    rows = _rows_since(user_id, since)

    counts: dict[str, int] = defaultdict(int)
    for scan_date, risk_level in rows:
        if only_threats and risk_level not in {RiskLevel.SUSPICIOUS, RiskLevel.DANGEROUS}:
            continue
        counts[scan_date.date().isoformat()] += 1

    today = utcnow().date()
    return [
        {"date": (today - timedelta(days=offset)).isoformat(), "count": counts.get((today - timedelta(days=offset)).isoformat(), 0)}
        for offset in range(days - 1, -1, -1)
    ]


def get_threat_trend(user_id: str, days: int = 14) -> list[dict]:
    return daily_buckets(user_id, days, only_threats=True)


def get_weekly_activity(user_id: str) -> list[dict]:
    return daily_buckets(user_id, 7, only_threats=False)


def get_monthly_activity(user_id: str) -> list[dict]:
    return daily_buckets(user_id, 30, only_threats=False)


def get_threat_heatmap(user_id: str, days: int = 90) -> list[dict]:
    """Scan counts by weekday (0=Monday..6=Sunday) and risk level, over the
    last `days` — a lightweight stand-in for a full hour x day grid, which
    would be too sparse to be meaningful for a single account."""
    since = utcnow() - __import__("datetime").timedelta(days=days)
    rows = _rows_since(user_id, since)

    grid = {weekday: {level: 0 for level in RiskLevel.ALL} for weekday in range(7)}
    for scan_date, risk_level in rows:
        if risk_level in grid[scan_date.weekday()]:
            grid[scan_date.weekday()][risk_level] += 1

    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return [{"weekday": weekday_names[day], **grid[day]} for day in range(7)]


def get_average_scan_duration_ms(user_id: str) -> float | None:
    total_sum = 0
    total_count = 0
    for model in _SCAN_MODELS:
        row_sum, row_count = (
            db.session.query(func.sum(model.duration_ms), func.count(model.duration_ms))
            .filter(model.user_id == user_id, model.duration_ms.isnot(None))
            .one()
        )
        if row_sum is not None:
            total_sum += row_sum
            total_count += row_count

    if total_count == 0:
        return None
    return round(total_sum / total_count, 1)


def get_most_dangerous_domains(user_id: str, limit: int = 5) -> list[dict]:
    return scan_analytics.most_dangerous_domains(user_id, limit)


def get_most_common_keywords(user_id: str, limit: int = 10) -> list[dict]:
    return scan_analytics.most_common_keywords(user_id, limit)


def get_dashboard_intelligence(user_id: str) -> dict:
    unified = unified_scan_service.get_unified_stats(user_id)
    by_type = unified["by_scanner_type"]
    most_common_scanner = max(by_type, key=lambda k: by_type[k]) if unified["total_scans"] > 0 else None

    return {
        "overall_security_score": unified["average_trust_score"],
        "threat_trend": get_threat_trend(user_id),
        "recent_threat_timeline": unified["latest_threats"],
        "weekly_activity": get_weekly_activity(user_id),
        "monthly_activity": get_monthly_activity(user_id),
        "scan_distribution": by_type,
        "risk_distribution": {
            "safe": unified["safe_count"],
            "low_risk": unified["low_risk_count"],
            "suspicious": unified["suspicious_count"],
            "dangerous": unified["dangerous_count"],
        },
        "most_dangerous_domains": get_most_dangerous_domains(user_id),
        "most_common_keywords": get_most_common_keywords(user_id),
        "most_common_scanner": most_common_scanner,
        "threat_heatmap": get_threat_heatmap(user_id),
        "average_scan_duration_ms": get_average_scan_duration_ms(user_id),
        "detection_accuracy": {
            "available": False,
            "message": "Detection accuracy requires labeled ground-truth data (confirmed true/false positives), "
            "which CyberShield doesn't collect yet. This will be enabled in a future phase.",
        },
        "recent_notifications": [n.to_dict() for n in notification_service.list_notifications(user_id, 1, 5)[0]],
        "unread_notification_count": notification_service.get_unread_count(user_id),
    }
