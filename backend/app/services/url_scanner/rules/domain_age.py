"""Flags recently-registered domains.

Phishing domains are typically registered days or weeks before use and
abandoned shortly after. Uses `domain_age_provider` for the actual
lookup so this rule stays agnostic to where that data comes from.
"""

from app.services.url_scanner.domain_age_provider import get_domain_age_provider
from app.services.url_scanner.domain_utils import registrable_domain
from app.services.url_scanner.types import RuleResult, ScanContext, Severity

MESSAGE_BY_STATUS = {
    "recently_registered": "Domain was registered recently.",
    "moderately_aged": "Domain is moderately aged.",
    "established": "Domain is well-established.",
    "unknown": "Domain registration date could not be determined.",
}

IMPACT_BY_STATUS = {
    "recently_registered": -15,
    "moderately_aged": -5,
    "established": 0,
    "unknown": 0,
}

SEVERITY_BY_STATUS = {
    "recently_registered": Severity.MEDIUM,
    "moderately_aged": Severity.LOW,
    "established": Severity.INFO,
    "unknown": Severity.INFO,
}


def evaluate(ctx: ScanContext) -> RuleResult:
    if ctx.is_ip_host or not ctx.hostname:
        return RuleResult(
            rule="domain_age",
            label="Domain Age",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="Not applicable.",
            detail="unknown",
        )

    domain = registrable_domain(ctx.hostname.lower())
    result = get_domain_age_provider().lookup(domain)

    return RuleResult(
        rule="domain_age",
        label="Domain Age",
        triggered=result.status in {"recently_registered", "moderately_aged"},
        impact=IMPACT_BY_STATUS[result.status],
        severity=SEVERITY_BY_STATUS[result.status],
        message=MESSAGE_BY_STATUS[result.status],
        detail=result.status,
    )
