"""Flags unusually long or unusually short URLs.

Phishing URLs are frequently padded with long, meaningless paths/query
strings to bury the real destination or evade simple pattern matching.
"""

from app.services.url_scanner.types import RuleResult, ScanContext, Severity
from app.services.url_scanner.whitelist import is_whitelisted_domain

VERY_LONG = 100
LONG = 75
VERY_SHORT = 12


def evaluate(ctx: ScanContext) -> RuleResult:
    if ctx.hostname:
        is_whitelisted, brand_name = is_whitelisted_domain(ctx.hostname)
        if is_whitelisted:
            return RuleResult(
                rule="url_length",
                label="URL Length",
                triggered=False,
                impact=0,
                severity=Severity.INFO,
                message=f"URL query on verified official domain for {brand_name} is within expected range.",
            )

    length = len(ctx.raw_url)

    if length >= VERY_LONG:
        return RuleResult(
            rule="url_length",
            label="URL Length",
            triggered=True,
            impact=-15,
            severity=Severity.MEDIUM,
            message=f"URL is unusually long ({length} characters).",
        )
    if length >= LONG:
        return RuleResult(
            rule="url_length",
            label="URL Length",
            triggered=True,
            impact=-8,
            severity=Severity.LOW,
            message=f"URL is longer than typical ({length} characters).",
        )
    if length <= VERY_SHORT:
        return RuleResult(
            rule="url_length",
            label="URL Length",
            triggered=True,
            impact=-3,
            severity=Severity.INFO,
            message=f"URL is unusually short ({length} characters).",
        )

    return RuleResult(
        rule="url_length",
        label="URL Length",
        triggered=False,
        impact=0,
        severity=Severity.INFO,
        message="URL length is within a normal range.",
    )
