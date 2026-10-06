import concurrent.futures
from dataclasses import asdict

from sqlalchemy import func

from app.constants import RiskLevel
from app.extensions import db
from app.models.email_scan import EmailScanHistory
from app.services import notification_service
from app.services.email_scanner.engine import analyze_email
from app.services.email_scanner.parser import parse_email_source
from app.utils.errors import APIError
from app.utils.timing import Stopwatch

RECENT_SCANS_LIMIT = 5

# A malformed .eml (e.g. a pathologically deep MIME multipart structure)
# could otherwise take a long time to parse on a request thread. Bounded by
# the same concurrent.futures timeout pattern url_scanner/engine.py already
# uses for its network-bound rules.
PARSE_TIMEOUT_SECONDS = 10


def _rule_results_to_dicts(rule_results) -> list[dict]:
    return [asdict(r) for r in rule_results]


def _parse_with_timeout(raw_source: str | bytes):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(parse_email_source, raw_source)
        try:
            return future.result(timeout=PARSE_TIMEOUT_SECONDS)
        except concurrent.futures.TimeoutError:
            raise APIError("This email took too long to parse and was rejected.", 422)
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def perform_and_store_email_scan(user_id: str, raw_source: str | bytes) -> EmailScanHistory:
    with Stopwatch() as sw:
        ctx = _parse_with_timeout(raw_source)
        report = analyze_email(ctx)

    scan_result = {
        "sender_display_name": report.sender_display_name,
        "sender_email": report.sender_email,
        "subject": report.subject,
        "trust_score": report.trust_score,
        "risk": report.risk_level,
        "reasons": report.reasons,
        "recommendations": report.recommendations,
        "links": [asdict(link) for link in report.links],
        "attachments": [asdict(attachment) for attachment in report.attachments],
    }
    analysis_details = {
        "rules": _rule_results_to_dicts(report.rule_results),
        "scanned_at": report.scanned_at.isoformat(),
    }

    record = EmailScanHistory(
        user_id=user_id,
        sender_display_name=report.sender_display_name,
        sender_email=report.sender_email,
        subject=report.subject,
        trust_score=report.trust_score,
        risk_level=report.risk_level,
        link_count=len(report.links),
        attachment_count=len(report.attachments),
        scan_result=scan_result,
        analysis_details=analysis_details,
        duration_ms=sw.elapsed_ms,
    )
    db.session.add(record)
    db.session.commit()

    notification_service.notify_scan_result(
        user_id, "email", report.risk_level, report.sender_email or "(unknown sender)", record.id
    )
    return record


def perform_ephemeral_email_scan(raw_source: str | bytes) -> dict:
    """Same detection engine as `perform_and_store_email_scan`, but nothing
    is written to the database — no EmailScanHistory row, no notification.
    Used by the public Guest/Quick Scan endpoints (no account required),
    mirroring `scan_service.perform_ephemeral_scan`'s existing pattern for
    URL scans.
    """
    with Stopwatch() as sw:
        ctx = _parse_with_timeout(raw_source)
        report = analyze_email(ctx)

    return {
        "sender_display_name": report.sender_display_name,
        "sender_email": report.sender_email,
        "subject": report.subject,
        "trust_score": report.trust_score,
        "risk": report.risk_level,
        "reasons": report.reasons,
        "recommendations": report.recommendations,
        "links": [asdict(link) for link in report.links],
        "attachments": [asdict(attachment) for attachment in report.attachments],
        "rules": _rule_results_to_dicts(report.rule_results),
        "scan_date": f"{report.scanned_at.isoformat()}Z",
        "duration_ms": sw.elapsed_ms,
        "persisted": False,
    }


def get_email_scan_history(
    user_id: str,
    page: int,
    per_page: int,
    search: str | None = None,
    risk_level: str | None = None,
) -> tuple[list[EmailScanHistory], int]:
    query = EmailScanHistory.query.filter_by(user_id=user_id)

    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                EmailScanHistory.sender_email.ilike(like),
                EmailScanHistory.sender_display_name.ilike(like),
                EmailScanHistory.subject.ilike(like),
            )
        )
    if risk_level:
        query = query.filter_by(risk_level=risk_level)

    query = query.order_by(EmailScanHistory.scan_date.desc())
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total


def get_email_scan_by_id(user_id: str, scan_id: int) -> EmailScanHistory | None:
    return EmailScanHistory.query.filter_by(id=scan_id, user_id=user_id).first()


def get_email_dashboard_stats(user_id: str) -> dict:
    base_query = EmailScanHistory.query.filter_by(user_id=user_id)
    total_scans = base_query.count()

    counts_by_risk = dict(
        db.session.query(EmailScanHistory.risk_level, func.count(EmailScanHistory.id))
        .filter(EmailScanHistory.user_id == user_id)
        .group_by(EmailScanHistory.risk_level)
        .all()
    )

    average_trust_score = (
        db.session.query(func.avg(EmailScanHistory.trust_score))
        .filter(EmailScanHistory.user_id == user_id)
        .scalar()
    )

    recent = base_query.order_by(EmailScanHistory.scan_date.desc()).limit(RECENT_SCANS_LIMIT).all()

    return {
        "total_emails_scanned": total_scans,
        "safe_count": counts_by_risk.get(RiskLevel.SAFE, 0),
        "low_risk_count": counts_by_risk.get(RiskLevel.LOW_RISK, 0),
        "suspicious_count": counts_by_risk.get(RiskLevel.SUSPICIOUS, 0),
        "dangerous_count": counts_by_risk.get(RiskLevel.DANGEROUS, 0),
        "average_trust_score": round(float(average_trust_score), 1) if average_trust_score is not None else None,
        "recent_scans": [scan.to_summary_dict() for scan in recent],
    }
