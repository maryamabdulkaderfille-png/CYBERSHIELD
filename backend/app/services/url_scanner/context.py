from ipaddress import ip_address
from urllib.parse import urlparse

from app.services.url_scanner.network import resolve_hostname
from app.services.url_scanner.types import ScanContext


def build_context(raw_url: str, resolve_dns: bool = True) -> ScanContext:
    """`resolve_dns=False` skips the real DNS lookup entirely — used by
    quick_classify, whose whole point is staying network-free. None of the
    CPU-only rules need `resolved_ips` (only the ssl_certificate rule does),
    so skipping it there costs nothing and avoids a slow/hanging lookup for
    every one of the (possibly dozens of) links in an email."""
    parsed = urlparse(raw_url)
    hostname = parsed.hostname or ""

    is_ip_host = False
    try:
        ip_address(hostname)
        is_ip_host = True
    except ValueError:
        pass

    if not resolve_dns:
        resolved_ips = []
    else:
        resolved_ips = [] if is_ip_host else resolve_hostname(hostname)

    return ScanContext(
        raw_url=raw_url,
        parsed=parsed,
        hostname=hostname,
        resolved_ips=resolved_ips,
        dns_resolved=bool(resolved_ips) or is_ip_host,
        is_ip_host=is_ip_host,
    )
