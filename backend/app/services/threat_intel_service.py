"""Threat Intelligence Center (Phase 5) — platform-wide (all users), unlike
the per-user Dashboard/Scan Center/Profile. Everything here is derived from
existing scan data (ScanHistory/EmailScanHistory/QRScanHistory) and the
existing BlacklistEntry table — no new detection logic, no fake data.

`ThreatFeedProvider` is the same "prepare architecture, don't fake the
feature" pattern already used for EmailService/DomainAgeProvider/
ReportExporter: an abstract interface plus one concrete implementation
backed by the platform's own data. Swapping in a real external feed (e.g.
PhishTank, OpenPhish) later is a matter of adding another provider class
and pointing `get_provider()` at it — nothing else changes.
"""

from abc import ABC, abstractmethod
from collections import Counter
from urllib.parse import urlparse

from app.constants import RiskLevel
from app.models.blacklist import BlacklistEntry
from app.models.email_scan import EmailScanHistory
from app.models.qr_scan import QRScanHistory
from app.models.scan import ScanHistory
from app.services import scan_analytics
from app.utils.cache import cacheable

_SEVERITY_RANK = {level: rank for rank, level in enumerate(RiskLevel.ALL)}


class ThreatFeedProvider(ABC):
    """Interface for a source of known-threat domains. `InternalThreatFeedProvider`
    is the only implementation today (the platform's own blacklist + scan
    history); a future phase can add a `LiveThreatFeedProvider` that polls an
    external feed (PhishTank, OpenPhish, etc.) without touching call sites."""

    @abstractmethod
    def known_phishing_domains(self, limit: int) -> list[dict]: ...


class InternalThreatFeedProvider(ThreatFeedProvider):
    def known_phishing_domains(self, limit: int) -> list[dict]:
        entries = BlacklistEntry.query.order_by(BlacklistEntry.created_at.desc()).limit(limit).all()
        return [
            {"domain": entry.domain, "reason": entry.reason, "added_at": f"{entry.created_at.isoformat()}Z"}
            for entry in entries
        ]


def get_provider() -> ThreatFeedProvider:
    return InternalThreatFeedProvider()


def _severity(level: str) -> int:
    return _SEVERITY_RANK.get(level, 0)


@cacheable(ttl_seconds=300)
def get_threat_statistics() -> dict:
    """Platform-wide totals. Cache-placeholder-decorated: this aggregates
    across every user's scans, so it's the most expensive query on this
    page and the first candidate for a real cache later."""
    total_scans = 0
    counts_by_risk = {level: 0 for level in RiskLevel.ALL}
    for model in (ScanHistory, EmailScanHistory, QRScanHistory):
        rows = model.query.with_entities(model.risk_level).all()
        total_scans += len(rows)
        for (risk_level,) in rows:
            if risk_level in counts_by_risk:
                counts_by_risk[risk_level] += 1

    blacklist_count = BlacklistEntry.query.count()

    return {
        "total_scans": total_scans,
        "safe_count": counts_by_risk[RiskLevel.SAFE],
        "low_risk_count": counts_by_risk[RiskLevel.LOW_RISK],
        "suspicious_count": counts_by_risk[RiskLevel.SUSPICIOUS],
        "dangerous_count": counts_by_risk[RiskLevel.DANGEROUS],
        "blacklisted_domains": blacklist_count,
    }


def get_severity_distribution() -> dict:
    stats = get_threat_statistics()
    return {
        "safe": stats["safe_count"],
        "low_risk": stats["low_risk_count"],
        "suspicious": stats["suspicious_count"],
        "dangerous": stats["dangerous_count"],
    }


def get_detection_trends(days: int = 14) -> list[dict]:
    from app.services import dashboard_service

    return dashboard_service.daily_buckets(None, days, only_threats=True)


def get_attack_categories(limit: int = 10) -> list[dict]:
    """Tally of which detection rule fired, across all scan types — a proxy
    for "attack category" (typosquatting, blacklist hit, suspicious keywords,
    urgency language, etc.) since the platform doesn't have a separate
    hand-labeled taxonomy."""
    counter: Counter = Counter()
    for model in (ScanHistory, EmailScanHistory, QRScanHistory):
        rows = (
            model.query.order_by(model.scan_date.desc())
            .limit(scan_analytics.ROWS_LIMIT)
            .with_entities(model.analysis_details)
            .all()
        )
        for (analysis_details,) in rows:
            for rule in analysis_details.get("rules", []):
                if rule.get("triggered"):
                    counter[rule.get("label", rule.get("rule", "Unknown"))] += 1
    return [{"category": category, "count": count} for category, count in counter.most_common(limit)]


def _domain_feed(search: str | None, risk_level: str | None) -> list[dict]:
    """Merged view: every domain seen in a scan, plus every blacklisted
    domain (even with zero recent scans), deduped by hostname."""
    feed: dict[str, dict] = {}

    rows = (
        ScanHistory.query.order_by(ScanHistory.scan_date.desc())
        .limit(scan_analytics.ROWS_LIMIT)
        .with_entities(ScanHistory.url, ScanHistory.risk_level, ScanHistory.scan_date)
        .all()
    )
    for url, level, scan_date in rows:
        domain = urlparse(url).hostname or url
        entry = feed.setdefault(
            domain, {"domain": domain, "count": 0, "risk_level": RiskLevel.SAFE, "last_seen": scan_date, "is_blacklisted": False}
        )
        entry["count"] += 1
        if scan_date > entry["last_seen"]:
            entry["last_seen"] = scan_date
        if _severity(level) > _severity(entry["risk_level"]):
            entry["risk_level"] = level

    for blacklist_entry in BlacklistEntry.query.all():
        entry = feed.setdefault(
            blacklist_entry.domain,
            {
                "domain": blacklist_entry.domain,
                "count": 0,
                "risk_level": RiskLevel.DANGEROUS,
                "last_seen": blacklist_entry.created_at,
                "is_blacklisted": False,
            },
        )
        entry["is_blacklisted"] = True
        entry["risk_level"] = RiskLevel.DANGEROUS

    items = list(feed.values())
    if search:
        needle = search.lower()
        items = [item for item in items if needle in item["domain"].lower()]
    if risk_level:
        items = [item for item in items if item["risk_level"] == risk_level]
    return items


def get_threat_domains(
    page: int, per_page: int, search: str | None = None, risk_level: str | None = None, sort_by: str = "count", sort_dir: str = "desc"
) -> tuple[list[dict], int]:
    items = _domain_feed(search, risk_level)

    sort_key = {
        "count": lambda item: item["count"],
        "last_seen": lambda item: item["last_seen"],
        "domain": lambda item: item["domain"],
    }.get(sort_by, lambda item: item["count"])
    items.sort(key=sort_key, reverse=(sort_dir != "asc"))

    total = len(items)
    start = (page - 1) * per_page
    page_items = items[start : start + per_page]
    return [
        {
            "domain": item["domain"],
            "count": item["count"],
            "risk_level": item["risk_level"],
            "last_seen": f"{item['last_seen'].isoformat()}Z",
            "is_blacklisted": item["is_blacklisted"],
        }
        for item in page_items
    ], total


def get_threat_intelligence_summary() -> dict:
    provider = get_provider()
    return {
        "known_phishing_domains": provider.known_phishing_domains(limit=10),
        "suspicious_domains": [
            item
            for item in _domain_feed(None, None)
            if item["risk_level"] == RiskLevel.SUSPICIOUS and not item["is_blacklisted"]
        ][:10],
        "recently_blocked_domains": scan_analytics.recently_blocked_domains(None, limit=10),
        "top_targeted_brands": scan_analytics.top_targeted_brands(None, limit=10),
        "most_common_keywords": scan_analytics.most_common_keywords(None, limit=10),
        "attack_categories": get_attack_categories(),
        "threat_statistics": get_threat_statistics(),
        "severity_distribution": get_severity_distribution(),
        "detection_trends": get_detection_trends(),
        "blacklist_overview": {
            "total": BlacklistEntry.query.count(),
            "entries": [
                {"domain": e.domain, "reason": e.reason, "added_at": f"{e.created_at.isoformat()}Z"}
                for e in BlacklistEntry.query.order_by(BlacklistEntry.created_at.desc()).limit(20).all()
            ],
        },
        "threat_feed_architecture": {
            "provider": type(provider).__name__,
            "live_feed_enabled": False,
            "message": "Threat feed data currently comes from CyberShield's own blacklist and scan history. "
            "The ThreatFeedProvider interface is ready for a live external feed (e.g. PhishTank/OpenPhish) "
            "to be plugged in as a future provider implementation.",
        },
    }
