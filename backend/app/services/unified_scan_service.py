"""The 'Scan Center' — a read/delete abstraction layer over the three
existing per-scanner history tables (ScanHistory, EmailScanHistory,
QRScanHistory).

Deliberately does NOT introduce a new merged table or migrate existing data:
each scanner keeps its own table (and its own dedicated API endpoints,
unchanged from Phases 2/3) exactly as before. This service only normalizes
and combines them for a unified list/search/stats view, via a SQL
UNION ALL — no scan data is duplicated or copied anywhere.

Phase 7 additive change: every public function's `user_id` is now
`str | None` — `None` means "every user" (platform-wide), used only by the
admin Scan Management screens. This is the same user_id-required-vs-None
generalization pattern already used by dashboard_service/scan_analytics/
threat_intel_service since Phase 5, applied here for the same reason:
one implementation serving both a per-user view and a platform-wide one.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import case, func, literal, select

from app.constants import RiskLevel
from app.extensions import db
from app.models.email_scan import EmailScanHistory
from app.models.qr_scan import QRScanHistory
from app.models.scan import ScanHistory
from app.models.user import User
from app.utils.time import utcnow

SCANNER_TYPES = ("url", "email", "qr")
RANGE_KEYS = ("today", "7d", "30d", "all")

_MODEL_BY_TYPE = {
    "url": ScanHistory,
    "email": EmailScanHistory,
    "qr": QRScanHistory,
}


def _target_summary_column(scanner_type: str):
    if scanner_type == "url":
        return ScanHistory.url
    if scanner_type == "email":
        return func.coalesce(EmailScanHistory.subject, EmailScanHistory.sender_email, "(unknown sender)")
    return QRScanHistory.raw_content


def _scan_select(scanner_type: str, user_id: str | None):
    model = _MODEL_BY_TYPE[scanner_type]
    query = (
        select(
            literal(scanner_type).label("scanner_type"),
            model.id.label("id"),
            model.user_id.label("user_id"),
            User.username.label("username"),
            _target_summary_column(scanner_type).label("target"),
            model.trust_score.label("trust_score"),
            model.risk_level.label("risk_level"),
            model.source.label("source"),
            model.scan_date.label("scan_date"),
        )
        .join(User, User.id == model.user_id)
    )
    if user_id is not None:
        query = query.where(model.user_id == user_id)
    return query


def _unified_subquery(user_id: str | None, scanner_type: str | None = None):
    types_to_include = [scanner_type] if scanner_type else list(SCANNER_TYPES)
    selects = [_scan_select(t, user_id) for t in types_to_include]
    combined = selects[0] if len(selects) == 1 else selects[0].union_all(*selects[1:])
    return combined.subquery()


@dataclass
class UnifiedScanFilters:
    scanner_type: str | None = None
    risk_level: str | None = None
    search: str | None = None
    trust_score_min: int | None = None
    trust_score_max: int | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    source: str | None = None
    sort_by: str = "scan_date"
    sort_dir: str = "desc"


def _apply_filters(query, subquery, filters: UnifiedScanFilters):
    if filters.risk_level:
        query = query.where(subquery.c.risk_level == filters.risk_level)
    if filters.search:
        query = query.where(subquery.c.target.ilike(f"%{filters.search}%"))
    if filters.trust_score_min is not None:
        query = query.where(subquery.c.trust_score >= filters.trust_score_min)
    if filters.trust_score_max is not None:
        query = query.where(subquery.c.trust_score <= filters.trust_score_max)
    if filters.date_from is not None:
        query = query.where(subquery.c.scan_date >= filters.date_from)
    if filters.date_to is not None:
        query = query.where(subquery.c.scan_date <= filters.date_to)
    if filters.source:
        query = query.where(subquery.c.source == filters.source)
    return query


def _serialize(row) -> dict:
    return {
        "scanner_type": row["scanner_type"],
        "id": row["id"],
        "user_id": row["user_id"],
        "username": row["username"],
        "target": row["target"],
        "trust_score": row["trust_score"],
        "risk_level": row["risk_level"],
        "source": row["source"],
        "scan_date": f"{row['scan_date'].isoformat()}Z",
    }


def get_unified_scans(
    user_id: str | None, page: int, per_page: int, filters: UnifiedScanFilters
) -> tuple[list[dict], int]:
    subquery = _unified_subquery(user_id, filters.scanner_type)

    count_query = _apply_filters(select(func.count()).select_from(subquery), subquery, filters)
    total = db.session.execute(count_query).scalar_one()

    sort_column = subquery.c.trust_score if filters.sort_by == "trust_score" else subquery.c.scan_date
    sort_column = sort_column.asc() if filters.sort_dir == "asc" else sort_column.desc()

    list_query = _apply_filters(select(subquery), subquery, filters)
    list_query = list_query.order_by(sort_column).offset((page - 1) * per_page).limit(per_page)

    rows = db.session.execute(list_query).mappings().all()
    items = [_serialize(row) for row in rows]
    return items, total


def get_scan_record(user_id: str | None, scanner_type: str, scan_id: int):
    if scanner_type not in _MODEL_BY_TYPE:
        return None
    model = _MODEL_BY_TYPE[scanner_type]
    query = model.query.filter_by(id=scan_id)
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    return query.first()


def delete_scan(user_id: str | None, scanner_type: str, scan_id: int) -> bool:
    record = get_scan_record(user_id, scanner_type, scan_id)
    if record is None:
        return False
    db.session.delete(record)
    db.session.commit()
    return True


def bulk_delete_scans(user_id: str | None, items: list[dict]) -> int:
    deleted = 0
    for item in items:
        record = get_scan_record(user_id, item.get("scanner_type", ""), item.get("id", -1))
        if record is not None:
            db.session.delete(record)
            deleted += 1
    db.session.commit()
    return deleted


def get_unified_stats(user_id: str | None) -> dict:
    subquery = _unified_subquery(user_id)

    total = db.session.execute(select(func.count()).select_from(subquery)).scalar_one()

    counts_by_risk = dict(
        db.session.execute(select(subquery.c.risk_level, func.count()).group_by(subquery.c.risk_level)).all()
    )
    counts_by_type = dict(
        db.session.execute(select(subquery.c.scanner_type, func.count()).group_by(subquery.c.scanner_type)).all()
    )
    average_trust_score = db.session.execute(select(func.avg(subquery.c.trust_score))).scalar_one()

    recent_rows = db.session.execute(
        select(subquery).order_by(subquery.c.scan_date.desc()).limit(5)
    ).mappings().all()

    threat_rows = db.session.execute(
        select(subquery)
        .where(subquery.c.risk_level.in_([RiskLevel.SUSPICIOUS, RiskLevel.DANGEROUS]))
        .order_by(subquery.c.scan_date.desc())
        .limit(5)
    ).mappings().all()

    top_risk_rows = db.session.execute(
        select(subquery).order_by(subquery.c.trust_score.asc()).limit(5)
    ).mappings().all()

    return {
        "total_scans": total,
        "safe_count": counts_by_risk.get(RiskLevel.SAFE, 0),
        "low_risk_count": counts_by_risk.get(RiskLevel.LOW_RISK, 0),
        "suspicious_count": counts_by_risk.get(RiskLevel.SUSPICIOUS, 0),
        "dangerous_count": counts_by_risk.get(RiskLevel.DANGEROUS, 0),
        "by_scanner_type": {
            "url": counts_by_type.get("url", 0),
            "email": counts_by_type.get("email", 0),
            "qr": counts_by_type.get("qr", 0),
        },
        "average_trust_score": round(float(average_trust_score), 1) if average_trust_score is not None else None,
        "recent_scans": [_serialize(r) for r in recent_rows],
        "latest_threats": [_serialize(r) for r in threat_rows],
        "top_risks": [_serialize(r) for r in top_risk_rows],
    }


def _range_since(range_key: str) -> datetime | None:
    """Start of the window for a Today/7d/30d/All-time filter. None means
    no lower bound (all time)."""
    now = utcnow()
    if range_key == "today":
        return datetime(now.year, now.month, now.day)
    if range_key == "7d":
        return now - timedelta(days=7)
    if range_key == "30d":
        return now - timedelta(days=30)
    return None


def get_unified_stats_range(user_id: str | None, range_key: str) -> dict:
    """Same aggregate shape as `get_unified_stats`, scoped to a date-range
    filter (Today/7 days/30 days/All time) for the dashboard's Unified
    Overview cards. Additive read-only query — does not alter or replace
    `get_unified_stats`, which remains used wherever an all-time view is
    wanted."""
    if range_key not in RANGE_KEYS:
        range_key = "all"
    since = _range_since(range_key)
    subquery = _unified_subquery(user_id)

    def _scoped(query):
        return query.where(subquery.c.scan_date >= since) if since is not None else query

    total = db.session.execute(_scoped(select(func.count()).select_from(subquery))).scalar_one()
    counts_by_risk = dict(
        db.session.execute(
            _scoped(select(subquery.c.risk_level, func.count()).group_by(subquery.c.risk_level))
        ).all()
    )
    counts_by_type = dict(
        db.session.execute(
            _scoped(select(subquery.c.scanner_type, func.count()).group_by(subquery.c.scanner_type))
        ).all()
    )
    average_trust_score = db.session.execute(_scoped(select(func.avg(subquery.c.trust_score)))).scalar_one()

    return {
        "range": range_key,
        "total_scans": total,
        "safe_count": counts_by_risk.get(RiskLevel.SAFE, 0),
        "low_risk_count": counts_by_risk.get(RiskLevel.LOW_RISK, 0),
        "suspicious_count": counts_by_risk.get(RiskLevel.SUSPICIOUS, 0),
        "dangerous_count": counts_by_risk.get(RiskLevel.DANGEROUS, 0),
        "by_scanner_type": {
            "url": counts_by_type.get("url", 0),
            "email": counts_by_type.get("email", 0),
            "qr": counts_by_type.get("qr", 0),
        },
        "average_trust_score": round(float(average_trust_score), 1) if average_trust_score is not None else None,
    }


def _window_totals(subquery, lo: datetime, hi: datetime) -> dict:
    query = (
        select(
            func.count().label("total"),
            func.sum(case((subquery.c.risk_level == RiskLevel.SAFE, 1), else_=0)).label("safe"),
            func.sum(
                case((subquery.c.risk_level.in_([RiskLevel.SUSPICIOUS, RiskLevel.DANGEROUS]), 1), else_=0)
            ).label("threats"),
            func.avg(subquery.c.trust_score).label("avg_trust"),
        )
        .select_from(subquery)
        .where(subquery.c.scan_date >= lo, subquery.c.scan_date < hi)
    )
    row = db.session.execute(query).one()
    return {
        "total": row.total or 0,
        "safe": int(row.safe or 0),
        "threats": int(row.threats or 0),
        "avg_trust": round(float(row.avg_trust), 1) if row.avg_trust is not None else None,
    }


def _delta_pct(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None or previous == 0:
        return None
    return round(((current - previous) / previous) * 100, 1)


def get_unified_stats_trend(user_id: str | None, days: int = 14) -> dict:
    """Period-over-period deltas (this week vs. last week) and a daily
    sparkline series for each of the 4 Unified Overview stat cards. Additive
    read-only query, built the same way dashboard_service.py's widgets are:
    Python-side bucketing over the existing union-all subquery, no new
    tables and no writes."""
    now = utcnow()
    current_since = now - timedelta(days=7)
    previous_since = now - timedelta(days=14)

    subquery = _unified_subquery(user_id)

    current = _window_totals(subquery, current_since, now)
    previous = _window_totals(subquery, previous_since, current_since)

    rows = db.session.execute(
        select(subquery.c.scan_date, subquery.c.risk_level, subquery.c.trust_score).where(
            subquery.c.scan_date >= now - timedelta(days=days)
        )
    ).all()

    daily_total: dict[str, int] = defaultdict(int)
    daily_safe: dict[str, int] = defaultdict(int)
    daily_threats: dict[str, int] = defaultdict(int)
    daily_trust_sum: dict[str, float] = defaultdict(float)
    daily_trust_count: dict[str, int] = defaultdict(int)

    for scan_date, risk_level, trust_score in rows:
        day = scan_date.date().isoformat()
        daily_total[day] += 1
        if risk_level == RiskLevel.SAFE:
            daily_safe[day] += 1
        if risk_level in (RiskLevel.SUSPICIOUS, RiskLevel.DANGEROUS):
            daily_threats[day] += 1
        if trust_score is not None:
            daily_trust_sum[day] += trust_score
            daily_trust_count[day] += 1

    day_list = [(now.date() - timedelta(days=offset)).isoformat() for offset in range(days - 1, -1, -1)]

    def _count_series(counts: dict[str, int]) -> list[dict]:
        return [{"date": d, "count": counts.get(d, 0)} for d in day_list]

    trust_series = [
        {
            "date": d,
            "value": round(daily_trust_sum[d] / daily_trust_count[d], 1) if daily_trust_count.get(d) else None,
        }
        for d in day_list
    ]

    return {
        "total_scans": {
            "current": current["total"],
            "previous": previous["total"],
            "delta_pct": _delta_pct(current["total"], previous["total"]),
            "series": _count_series(daily_total),
        },
        "safe_count": {
            "current": current["safe"],
            "previous": previous["safe"],
            "delta_pct": _delta_pct(current["safe"], previous["safe"]),
            "series": _count_series(daily_safe),
        },
        "threats_count": {
            "current": current["threats"],
            "previous": previous["threats"],
            "delta_pct": _delta_pct(current["threats"], previous["threats"]),
            "series": _count_series(daily_threats),
        },
        "average_trust_score": {
            "current": current["avg_trust"],
            "previous": previous["avg_trust"],
            "delta_pct": _delta_pct(current["avg_trust"], previous["avg_trust"]),
            "series": trust_series,
        },
    }
