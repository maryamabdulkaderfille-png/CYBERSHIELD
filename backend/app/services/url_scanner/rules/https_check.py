"""Flags URLs that don't use HTTPS at all."""

from app.services.url_scanner.types import RuleResult, ScanContext, Severity


def evaluate(ctx: ScanContext) -> RuleResult:
    if ctx.parsed.scheme != "https":
        return RuleResult(
            rule="https_check",
            label="HTTPS",
            triggered=True,
            impact=-15,
            severity=Severity.MEDIUM,
            message="Site does not use HTTPS — traffic is unencrypted.",
        )

    return RuleResult(
        rule="https_check",
        label="HTTPS",
        triggered=False,
        impact=0,
        severity=Severity.INFO,
        message="Site uses HTTPS.",
    )
