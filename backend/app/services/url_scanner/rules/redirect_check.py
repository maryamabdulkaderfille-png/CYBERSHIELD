"""Follows the URL's redirect chain (if any) and flags suspicious patterns:
long chains, or a final destination on a different domain than the one
the user submitted. All hops are validated against the SSRF allowlist
in `network.safe_follow_redirects`.
"""

from app.services.url_scanner.network import safe_follow_redirects
from app.services.url_scanner.types import RuleResult, ScanContext, Severity


def evaluate(ctx: ScanContext) -> RuleResult:
    if ctx.parsed.scheme not in {"http", "https"} or not ctx.hostname:
        return RuleResult(
            rule="redirect_check",
            label="Redirect Chain",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="Not applicable.",
        )

    result = safe_follow_redirects(ctx.raw_url, ctx.hostname)

    if not result.ok:
        return RuleResult(
            rule="redirect_check",
            label="Redirect Chain",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="Redirect chain could not be checked.",
            detail=result.error,
        )

    hop_count = len(result.hops) - 1  # number of actual redirects, not the final request
    if hop_count <= 0:
        return RuleResult(
            rule="redirect_check",
            label="Redirect Chain",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="No redirects detected.",
        )

    impact = 0
    findings = [f"{hop_count} redirect(s) before reaching the final destination"]
    severity = Severity.LOW

    if hop_count > 3:
        impact -= 10
        severity = Severity.MEDIUM
        findings.append("longer redirect chain than typical")

    if result.cross_domain:
        impact -= 10
        severity = Severity.MEDIUM
        findings.append(f"redirects to a different domain ({result.final_url})")

    return RuleResult(
        rule="redirect_check",
        label="Redirect Chain",
        triggered=impact < 0,
        impact=impact,
        severity=severity,
        message="; ".join(findings).capitalize() + ".",
    )
