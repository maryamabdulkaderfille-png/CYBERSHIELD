"""Flags unusually deep subdomain chains.

Phishing kits often bury the real (attacker-controlled) domain under many
subdomain labels that spell out a brand name, e.g.
`secure-login.paypal.com.verify-account.example.net`.
"""

from app.services.url_scanner.types import RuleResult, ScanContext, Severity


def evaluate(ctx: ScanContext) -> RuleResult:
    if ctx.is_ip_host or not ctx.hostname:
        return RuleResult(
            rule="subdomains",
            label="Subdomains",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="Not applicable.",
        )

    labels = [label for label in ctx.hostname.split(".") if label]
    subdomain_count = max(len(labels) - 2, 0)

    if subdomain_count >= 4:
        return RuleResult(
            rule="subdomains",
            label="Subdomains",
            triggered=True,
            impact=-15,
            severity=Severity.HIGH,
            message=f"Unusually deep subdomain chain ({subdomain_count} subdomains).",
        )
    if subdomain_count >= 3:
        return RuleResult(
            rule="subdomains",
            label="Subdomains",
            triggered=True,
            impact=-8,
            severity=Severity.MEDIUM,
            message=f"More subdomains than typical ({subdomain_count} subdomains).",
        )

    return RuleResult(
        rule="subdomains",
        label="Subdomains",
        triggered=False,
        impact=0,
        severity=Severity.INFO,
        message="Subdomain depth is normal.",
    )
