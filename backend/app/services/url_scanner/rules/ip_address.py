"""Flags URLs that use a raw IP address instead of a domain name.

Legitimate sites are almost always accessed by domain name; a bare IP
(e.g. http://192.168.10.2/login) is a strong phishing indicator since it
avoids leaving a registrable domain behind.
"""

from app.services.url_scanner.types import RuleResult, ScanContext, Severity


def evaluate(ctx: ScanContext) -> RuleResult:
    if ctx.is_ip_host:
        return RuleResult(
            rule="ip_address",
            label="IP Address Host",
            triggered=True,
            impact=-30,
            severity=Severity.HIGH,
            message=f"Uses a raw IP address ({ctx.hostname}) instead of a domain name.",
        )

    return RuleResult(
        rule="ip_address",
        label="IP Address Host",
        triggered=False,
        impact=0,
        severity=Severity.INFO,
        message="Uses a domain name, not a raw IP address.",
    )
