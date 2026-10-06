from dataclasses import asdict

from sqlalchemy import func

from app.extensions import db
from app.models.scan import RiskLevelChoices, ScanHistory
from app.services import notification_service
from app.services.url_scanner.engine import scan_url
from app.utils.timing import Stopwatch

RECENT_SCANS_LIMIT = 5


def _rule_results_to_dicts(rule_results) -> list[dict]:
    return [asdict(r) for r in rule_results]


def perform_and_store_scan(user_id: str, url: str, source: str = "web") -> ScanHistory:
    with Stopwatch() as sw:
        report = scan_url(url)

    scan_result = {
        "trust_score": report.trust_score,
        "risk": report.risk_level,
        "reasons": report.reasons,
        "recommendations": report.recommendations,
    }
    analysis_details = {
        "rules": _rule_results_to_dicts(report.rule_results),
        "scanned_at": report.scanned_at.isoformat(),
    }

    record = ScanHistory(
        user_id=user_id,
        url=url,
        trust_score=report.trust_score,
        risk_level=report.risk_level,
        scan_result=scan_result,
        analysis_details=analysis_details,
        duration_ms=sw.elapsed_ms,
        source=source,
    )
    db.session.add(record)
    db.session.commit()

    notification_service.notify_scan_result(user_id, "url", report.risk_level, url, record.id)
    return record


def perform_ephemeral_scan(url: str) -> dict:
    """Same detection engine as `perform_and_store_scan`, but nothing is
    written to the database — no ScanHistory row, no notification, no
    dashboard/stats impact. Used only by the browser extension's Privacy
    Mode (Phase 6), where the user has opted out of having their automatic,
    every-page-visited scans logged against their account.
    """
    with Stopwatch() as sw:
        report = scan_url(url)

    return {
        "url": url,
        "trust_score": report.trust_score,
        "risk": report.risk_level,
        "reasons": report.reasons,
        "recommendations": report.recommendations,
        "rules": _rule_results_to_dicts(report.rule_results),
        "scan_date": f"{report.scanned_at.isoformat()}Z",
        "duration_ms": sw.elapsed_ms,
        "persisted": False,
    }


def get_scan_history(
    user_id: str,
    page: int,
    per_page: int,
    search: str | None = None,
    risk_level: str | None = None,
) -> tuple[list[ScanHistory], int]:
    query = ScanHistory.query.filter_by(user_id=user_id)

    if search:
        query = query.filter(ScanHistory.url.ilike(f"%{search}%"))
    if risk_level:
        query = query.filter_by(risk_level=risk_level)

    query = query.order_by(ScanHistory.scan_date.desc())
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total


def get_scan_by_id(user_id: str, scan_id: int) -> ScanHistory | None:
    return ScanHistory.query.filter_by(id=scan_id, user_id=user_id).first()


def get_dashboard_stats(user_id: str) -> dict:
    base_query = ScanHistory.query.filter_by(user_id=user_id)
    total_scans = base_query.count()

    counts_by_risk = dict(
        db.session.query(ScanHistory.risk_level, func.count(ScanHistory.id))
        .filter(ScanHistory.user_id == user_id)
        .group_by(ScanHistory.risk_level)
        .all()
    )

    average_trust_score = (
        db.session.query(func.avg(ScanHistory.trust_score)).filter(ScanHistory.user_id == user_id).scalar()
    )

    recent = base_query.order_by(ScanHistory.scan_date.desc()).limit(RECENT_SCANS_LIMIT).all()

    return {
        "total_scans": total_scans,
        "safe_count": counts_by_risk.get(RiskLevelChoices.SAFE, 0),
        "low_risk_count": counts_by_risk.get(RiskLevelChoices.LOW_RISK, 0),
        "suspicious_count": counts_by_risk.get(RiskLevelChoices.SUSPICIOUS, 0),
        "dangerous_count": counts_by_risk.get(RiskLevelChoices.DANGEROUS, 0),
        "average_trust_score": round(float(average_trust_score), 1) if average_trust_score is not None else None,
        "recent_scans": [scan.to_summary_dict() for scan in recent],
    }
