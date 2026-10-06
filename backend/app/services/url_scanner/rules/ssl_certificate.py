"""Validates the TLS certificate presented by the destination host.

Only runs a real handshake when the URL uses HTTPS in the first place;
HTTP-only sites are already penalized by the https_check rule.
"""

from app.services.url_scanner.network import get_certificate_info
from app.services.url_scanner.types import RuleResult, ScanContext, Severity

IMPACT_BY_STATUS = {
    "invalid": -20,
    "expired": -20,
    "unknown": -5,
    "valid": 0,
}

SEVERITY_BY_STATUS = {
    "invalid": Severity.HIGH,
    "expired": Severity.HIGH,
    "unknown": Severity.LOW,
    "valid": Severity.INFO,
}

MESSAGE_BY_STATUS = {
    "invalid": "SSL certificate is invalid or could not be verified.",
    "expired": "SSL certificate has expired.",
    "unknown": "SSL certificate status could not be determined.",
    "valid": "SSL certificate is valid.",
}

# Finer-grained messages for status=="unknown", so the report can tell a
# user "we couldn't check" apart from "this looks wrong" — without changing
# the status/impact/severity, which stay keyed off `info.status` alone (see
# IMPACT_BY_STATUS/SEVERITY_BY_STATUS above). Falls back to MESSAGE_BY_STATUS
# when no specific reason was determined.
MESSAGE_BY_REASON = {
    "dns_unresolved": "SSL certificate could not be checked — the hostname did not resolve.",
    "timeout": "SSL certificate could not be checked — the connection timed out.",
    "connection_failed": "SSL certificate could not be checked — the connection failed.",
    "ssl_error": "SSL certificate could not be checked due to a TLS protocol/handshake error.",
    "unsafe_host": "SSL certificate could not be checked — the hostname resolved to a non-public address.",
}


def evaluate(ctx: ScanContext) -> RuleResult:
    if ctx.parsed.scheme != "https":
        return RuleResult(
            rule="ssl_certificate",
            label="SSL Certificate",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="Not applicable — site does not use HTTPS.",
            detail="unknown",
        )

    info = get_certificate_info(ctx.hostname, ctx.resolved_ips)
    message = MESSAGE_BY_REASON.get(info.reason, MESSAGE_BY_STATUS[info.status])

    return RuleResult(
        rule="ssl_certificate",
        label="SSL Certificate",
        triggered=info.status in {"invalid", "expired", "unknown"},
        impact=IMPACT_BY_STATUS[info.status],
        severity=SEVERITY_BY_STATUS[info.status],
        message=message,
        detail=info.reason or info.status,
    )
