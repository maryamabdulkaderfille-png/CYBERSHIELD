"""Extended profile data (Phase 5): profile field updates + a stats summary
built entirely from existing services — no scan data is re-queried or
duplicated here.
"""

from app.extensions import db
from app.services import unified_scan_service

UPDATABLE_PROFILE_FIELDS = ("phone", "country", "bio", "avatar_url")


def update_profile_fields(user, data: dict):
    """Explicit allow-list update — the schema also restricts input, but this
    is a second guard against mass assignment if that ever changes."""
    for field in UPDATABLE_PROFILE_FIELDS:
        if field not in data:
            continue
        value = data[field]
        if field == "country" and value:
            value = value.upper()
        setattr(user, field, value)
    db.session.commit()
    return user


def get_profile_stats(user_id: str) -> dict:
    unified = unified_scan_service.get_unified_stats(user_id)

    return {
        "total_scans": unified["total_scans"],
        "safe_scans": unified["safe_count"] + unified["low_risk_count"],
        "dangerous_scans": unified["suspicious_count"] + unified["dangerous_count"],
        # Every scan has a report available on demand (report_service.build_report
        # works for any scan) — there's no separate "generate report" action to
        # count, so this intentionally equals total_scans rather than tracking a
        # second, redundant counter.
        "reports_generated": unified["total_scans"],
        "url_scans": unified["by_scanner_type"]["url"],
        "email_scans": unified["by_scanner_type"]["email"],
        "qr_scans": unified["by_scanner_type"]["qr"],
        "security_score": unified["average_trust_score"],
        "recent_activity": unified["recent_scans"],
    }
