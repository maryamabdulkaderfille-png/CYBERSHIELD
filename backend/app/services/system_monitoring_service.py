"""System Monitoring (Phase 7) — reads the in-memory request-metrics ring
buffer (app/middleware/request_metrics.py) plus a couple of cheap, real
checks (DB connectivity, process uptime). Memory usage is an honest,
labeled placeholder (see get_memory_usage) rather than a fabricated number —
the same pattern already used for "Detection Accuracy" in Phase 5.
"""

import os
from datetime import datetime, timezone

from flask import current_app
from sqlalchemy import text

from app.extensions import db
from app.middleware import request_metrics

RECENT_WINDOW_MINUTES = 5


def get_request_metrics() -> dict:
    samples = request_metrics.get_samples()
    if not samples:
        return {
            "total_requests": 0,
            "average_response_time_ms": None,
            "error_rate_percent": None,
            "requests_last_5_min": 0,
        }

    now = datetime.now(timezone.utc)
    recent = [s for s in samples if (now - s["at"]).total_seconds() <= RECENT_WINDOW_MINUTES * 60]
    error_count = sum(1 for s in samples if s["status"] >= 400)

    return {
        "total_requests": len(samples),
        "average_response_time_ms": round(sum(s["duration_ms"] for s in samples) / len(samples), 2),
        "error_rate_percent": round((error_count / len(samples)) * 100, 2),
        "requests_last_5_min": len(recent),
    }


def get_database_status() -> dict:
    try:
        db.session.execute(text("SELECT 1"))
        return {"status": "healthy", "message": "Database connection OK."}
    except Exception as exc:  # a monitoring check must never itself 500
        return {"status": "unhealthy", "message": str(exc)}


def get_memory_usage() -> dict:
    """Deliberately a placeholder: measuring real process memory needs a
    dependency (psutil) this project doesn't otherwise need — honestly
    labeled as unavailable rather than fabricated, same pattern as
    Detection Accuracy (Phase 5)."""
    return {"available": False, "message": "Memory usage monitoring is not yet implemented in this version of CyberShield."}


def get_uptime_seconds() -> float:
    started_at = request_metrics.get_process_started_at()
    return (datetime.now(timezone.utc) - started_at).total_seconds()


def get_threat_intelligence_status() -> dict:
    """Whether each external threat-intel provider has credentials
    configured — never the credential values themselves. A missing key
    means that provider's checks report UNAVAILABLE on every scan (see
    `url_scanner.rules.external_threat_intel`), which otherwise isn't
    visible anywhere until an admin reads an individual scan's rule
    breakdown; this surfaces it at a glance."""
    urlhaus_configured = bool(current_app.config.get("URLHAUS_AUTH_KEY") or os.getenv("URLHAUS_AUTH_KEY"))
    virustotal_configured = bool(current_app.config.get("VIRUSTOTAL_API_KEY") or os.getenv("VIRUSTOTAL_API_KEY"))
    return {
        "urlhaus": {"configured": urlhaus_configured},
        "virustotal": {"configured": virustotal_configured},
    }


def get_system_health() -> dict:
    return {
        "request_metrics": get_request_metrics(),
        "database": get_database_status(),
        "memory": get_memory_usage(),
        "threat_intelligence": get_threat_intelligence_status(),
        "uptime_seconds": round(get_uptime_seconds(), 1),
    }
