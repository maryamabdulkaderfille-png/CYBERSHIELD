"""Builds a structured, normalized 'report' view for any completed scan
(URL, email, or QR) — read-only and computed on demand from the existing
scan record. No separate 'Report' table or duplicated storage: a report is
just a consistent presentation of data the relevant scanner already
persisted.
"""

from datetime import datetime, timezone

from app.services.unified_scan_service import get_scan_record
from app.utils.errors import APIError


def _summary_for(scanner_type: str, detail: dict) -> tuple[str, str]:
    """Returns (target, summary_sentence)."""
    risk = detail.get("risk", "Unknown")
    score = detail.get("trust_score")

    if scanner_type == "url":
        target = detail["url"]
        return target, f"This URL scan of {target} completed with a trust score of {score}/100, classified as {risk}."

    if scanner_type == "email":
        sender = detail.get("sender_email") or "an unknown sender"
        subject = detail.get("subject") or "(no subject)"
        target = f"{sender} — {subject}"
        return (
            target,
            f"This email from {sender} (\"{subject}\") was classified as {risk} with a trust score of {score}/100.",
        )

    content_type = detail.get("content_type", "unknown")
    target = detail.get("raw_content", "")
    return (
        target,
        f"This QR code (type: {content_type}) was classified as {risk} with a trust score of {score}/100.",
    )


def build_report(user, scanner_type: str, scan_id: int) -> dict:
    record = get_scan_record(user.id, scanner_type, scan_id)
    if record is None:
        raise APIError("Scan not found.", 404)

    detail = record.to_detail_dict()
    target, summary = _summary_for(scanner_type, detail)

    return {
        "report_id": f"{scanner_type}-{scan_id}",
        "scanner_type": scanner_type,
        "scan_id": scan_id,
        "generated_at": datetime.now(timezone.utc).isoformat() + "Z",
        "scan_date": detail["scan_date"],
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
        },
        "target": target,
        "trust_score": detail["trust_score"],
        "risk_level": detail["risk"],
        "summary": summary,
        "findings": {
            "reasons": detail["reasons"],
            "rules": detail["rules"],
        },
        "recommendations": detail["recommendations"],
        "raw": detail,
    }
