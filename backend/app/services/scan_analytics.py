"""Aggregation helpers shared between the per-user dashboard
(dashboard_service, user_id required) and the platform-wide Threat
Intelligence Center (threat_intel_service, user_id=None) — factored out
here so the "parse rule details, tally" logic isn't duplicated between
the two call sites.

Everything reads existing rule output (analysis_details.rules[].detail)
already computed by the Phase 2/3 scanner engines — no detection logic
is re-implemented here.
"""

from collections import Counter
from urllib.parse import urlparse

from app.constants import RiskLevel
from app.models.email_scan import EmailScanHistory
from app.models.scan import ScanHistory

ROWS_LIMIT = 500  # bound on rows scanned per aggregation query

KEYWORD_RULE_NAMES = {"suspicious_keywords", "subject_analysis", "urgency_detection", "threat_language"}
BRAND_RULE_NAME = "typosquatting"
BLACKLIST_RULE_NAME = "blacklist_check"


def most_common_keywords(user_id: str | None, limit: int = 10) -> list[dict]:
    counter: Counter = Counter()
    for model in (ScanHistory, EmailScanHistory):
        query = model.query
        if user_id is not None:
            query = query.filter(model.user_id == user_id)
        rows = (
            query.order_by(model.scan_date.desc())
            .limit(ROWS_LIMIT)
            .with_entities(model.analysis_details)
            .all()
        )
        for (analysis_details,) in rows:
            for rule in analysis_details.get("rules", []):
                if rule.get("rule") in KEYWORD_RULE_NAMES and rule.get("triggered") and rule.get("detail"):
                    for term in rule["detail"].split(","):
                        term = term.strip()
                        if term:
                            counter[term] += 1
    return [{"keyword": keyword, "count": count} for keyword, count in counter.most_common(limit)]


def most_dangerous_domains(user_id: str | None, limit: int = 5) -> list[dict]:
    query = ScanHistory.query.filter(ScanHistory.risk_level == RiskLevel.DANGEROUS)
    if user_id is not None:
        query = query.filter(ScanHistory.user_id == user_id)
    rows = query.order_by(ScanHistory.scan_date.desc()).limit(ROWS_LIMIT).with_entities(ScanHistory.url).all()

    counter: Counter = Counter()
    for (url,) in rows:
        hostname = urlparse(url).hostname or url
        counter[hostname] += 1
    return [{"domain": domain, "count": count} for domain, count in counter.most_common(limit)]


def top_targeted_brands(user_id: str | None, limit: int = 10) -> list[dict]:
    query = ScanHistory.query
    if user_id is not None:
        query = query.filter(ScanHistory.user_id == user_id)
    rows = query.order_by(ScanHistory.scan_date.desc()).limit(ROWS_LIMIT).with_entities(ScanHistory.analysis_details).all()

    counter: Counter = Counter()
    for (analysis_details,) in rows:
        for rule in analysis_details.get("rules", []):
            if rule.get("rule") == BRAND_RULE_NAME and rule.get("triggered") and rule.get("detail"):
                counter[rule["detail"]] += 1
    return [{"brand": brand, "count": count} for brand, count in counter.most_common(limit)]


def recently_blocked_domains(user_id: str | None, limit: int = 10) -> list[dict]:
    """Scans where the blacklist_check rule triggered — i.e. the domain
    matched CyberShield's known-malicious list, not just a heuristic score."""
    query = ScanHistory.query
    if user_id is not None:
        query = query.filter(ScanHistory.user_id == user_id)
    rows = (
        query.order_by(ScanHistory.scan_date.desc())
        .limit(ROWS_LIMIT)
        .with_entities(ScanHistory.url, ScanHistory.analysis_details, ScanHistory.scan_date)
        .all()
    )

    blocked = []
    for url, analysis_details, scan_date in rows:
        for rule in analysis_details.get("rules", []):
            if rule.get("rule") == BLACKLIST_RULE_NAME and rule.get("triggered"):
                blocked.append(
                    {
                        "domain": urlparse(url).hostname or url,
                        "reason": rule.get("detail"),
                        "blocked_at": f"{scan_date.isoformat()}Z",
                    }
                )
                break
        if len(blocked) >= limit:
            break
    return blocked
