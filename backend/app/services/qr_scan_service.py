from dataclasses import asdict

from sqlalchemy import func

from app.constants import RiskLevel
from app.extensions import db
from app.models.qr_scan import QRScanHistory
from app.services import notification_service
from app.services.qr_scanner.decoder import decode_qr_image
from app.services.qr_scanner.engine import analyze_qr_content
from app.utils.timing import Stopwatch

RECENT_SCANS_LIMIT = 5


def perform_and_store_qr_scan(user_id: str, image_content: bytes) -> QRScanHistory:
    with Stopwatch() as sw:
        raw_content = decode_qr_image(image_content)
        report = analyze_qr_content(raw_content)

    scan_result = {
        "content_type": report.content_type,
        "raw_content": report.raw_content,
        "parsed_fields": report.parsed_fields,
        "trust_score": report.trust_score,
        "risk": report.risk_level,
        "reasons": report.reasons,
        "recommendations": report.recommendations,
    }
    analysis_details = {
        "rules": [asdict(r) for r in report.rule_results],
        "scanned_at": report.scanned_at.isoformat(),
    }

    record = QRScanHistory(
        user_id=user_id,
        content_type=report.content_type,
        raw_content=report.raw_content,
        trust_score=report.trust_score,
        risk_level=report.risk_level,
        scan_result=scan_result,
        analysis_details=analysis_details,
        duration_ms=sw.elapsed_ms,
    )
    db.session.add(record)
    db.session.commit()

    notification_service.notify_scan_result(user_id, "qr", report.risk_level, report.raw_content, record.id)
    return record


def perform_ephemeral_qr_scan(image_content: bytes) -> dict:
    """Same detection engine as `perform_and_store_qr_scan`, but nothing is
    written to the database — no QRScanHistory row, no notification. Used
    by the public Guest/Quick Scan endpoints (no account required),
    mirroring `scan_service.perform_ephemeral_scan`'s existing pattern for
    URL scans.
    """
    with Stopwatch() as sw:
        raw_content = decode_qr_image(image_content)
        report = analyze_qr_content(raw_content)

    return {
        "content_type": report.content_type,
        "raw_content": report.raw_content,
        "parsed_fields": report.parsed_fields,
        "trust_score": report.trust_score,
        "risk": report.risk_level,
        "reasons": report.reasons,
        "recommendations": report.recommendations,
        "rules": [asdict(r) for r in report.rule_results],
        "scan_date": f"{report.scanned_at.isoformat()}Z",
        "duration_ms": sw.elapsed_ms,
        "persisted": False,
    }


def get_qr_scan_history(
    user_id: str,
    page: int,
    per_page: int,
    search: str | None = None,
    risk_level: str | None = None,
) -> tuple[list[QRScanHistory], int]:
    query = QRScanHistory.query.filter_by(user_id=user_id)

    if search:
        query = query.filter(QRScanHistory.raw_content.ilike(f"%{search}%"))
    if risk_level:
        query = query.filter_by(risk_level=risk_level)

    query = query.order_by(QRScanHistory.scan_date.desc())
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total


def get_qr_scan_by_id(user_id: str, scan_id: int) -> QRScanHistory | None:
    return QRScanHistory.query.filter_by(id=scan_id, user_id=user_id).first()


def get_qr_dashboard_stats(user_id: str) -> dict:
    base_query = QRScanHistory.query.filter_by(user_id=user_id)
    total_scans = base_query.count()

    counts_by_risk = dict(
        db.session.query(QRScanHistory.risk_level, func.count(QRScanHistory.id))
        .filter(QRScanHistory.user_id == user_id)
        .group_by(QRScanHistory.risk_level)
        .all()
    )

    average_trust_score = (
        db.session.query(func.avg(QRScanHistory.trust_score)).filter(QRScanHistory.user_id == user_id).scalar()
    )

    recent = base_query.order_by(QRScanHistory.scan_date.desc()).limit(RECENT_SCANS_LIMIT).all()

    return {
        "total_qr_scanned": total_scans,
        "safe_count": counts_by_risk.get(RiskLevel.SAFE, 0),
        "low_risk_count": counts_by_risk.get(RiskLevel.LOW_RISK, 0),
        "suspicious_count": counts_by_risk.get(RiskLevel.SUSPICIOUS, 0),
        "dangerous_count": counts_by_risk.get(RiskLevel.DANGEROUS, 0),
        "average_trust_score": round(float(average_trust_score), 1) if average_trust_score is not None else None,
        "recent_scans": [scan.to_summary_dict() for scan in recent],
    }
