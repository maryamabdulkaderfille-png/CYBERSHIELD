"""Checks if the scanned URL belongs to a verified, high-reputation domain.

Provides explicit trust reinforcement for authentic platforms (Google,
Microsoft, Apple, GitHub, etc.) and protects users from false alarms
on legitimate corporate and consumer web properties.
"""

from app.services.url_scanner.types import RuleResult, ScanContext, Severity
from app.services.url_scanner.whitelist import is_whitelisted_domain


def evaluate(ctx: ScanContext) -> RuleResult:
    if ctx.is_ip_host or not ctx.hostname:
        return RuleResult(
            rule="whitelist_check",
            label="Verified Safe List",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="Not applicable for direct IP addresses.",
        )

    is_whitelisted, brand_name = is_whitelisted_domain(ctx.hostname)
    if is_whitelisted:
        return RuleResult(
            rule="whitelist_check",
            label="Verified Safe List",
            triggered=True,
            impact=15,  # positive trust reinforcement
            severity=Severity.INFO,
            message=f"Verified authentic domain for {brand_name} (CyberShield Global Safe List).",
            detail=brand_name,
        )

    return RuleResult(
        rule="whitelist_check",
        label="Verified Safe List",
        triggered=False,
        impact=0,
        severity=Severity.INFO,
        message="Domain is not on the Global Safe List (scanned using standard heuristic rules).",
    )
