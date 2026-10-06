"""Checks the scanned domain against the CyberShield blacklist table.

The blacklist is currently populated manually (or via tests); an admin
UI for managing it is planned for a later phase.
"""

from app.models.blacklist import BlacklistEntry
from app.services.url_scanner.domain_utils import registrable_domain
from app.services.url_scanner.types import RuleResult, ScanContext, Severity


def evaluate(ctx: ScanContext) -> RuleResult:
    if not ctx.hostname:
        return RuleResult(
            rule="blacklist_check",
            label="Blacklist",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="Not applicable.",
        )

    domain = registrable_domain(ctx.hostname.lower())
    entry = BlacklistEntry.query.filter(
        BlacklistEntry.domain.in_({ctx.hostname.lower(), domain}),
        BlacklistEntry.enabled.is_(True),
    ).first()

    if entry:
        return RuleResult(
            rule="blacklist_check",
            label="Blacklist",
            triggered=True,
            impact=-100,
            severity=Severity.CRITICAL,
            message=f"Domain appears on the CyberShield blacklist ({entry.reason}).",
            detail=entry.reason,
        )

    return RuleResult(
        rule="blacklist_check",
        label="Blacklist",
        triggered=False,
        impact=0,
        severity=Severity.INFO,
        message="Domain does not appear on the blacklist.",
    )
