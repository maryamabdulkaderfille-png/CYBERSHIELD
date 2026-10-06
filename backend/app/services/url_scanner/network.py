"""SSRF-safe outbound networking helpers.

The scanner makes real network calls (DNS, TLS handshake, HTTP HEAD) against
a URL supplied by the user. Without guards, that turns the scan endpoint into
an SSRF proxy — an attacker could submit `http://169.254.169.254/`,
`http://localhost:6379`, or an internal hostname and use the server to probe
its own network. Every helper here resolves the hostname first and refuses
to talk to anything that isn't a public, routable address.

Resolving and validating a hostname and then handing that same hostname to a
library that resolves it *again* to actually connect (as `requests` does)
leaves a DNS-rebinding window: the name can point somewhere safe at
validation time and somewhere internal a moment later, at connection time.
Every real connection below is made directly to the IP address that was
already validated — never a hostname — closing that window. TLS SNI and
certificate hostname verification still use the real hostname, via
`server_hostname`/`assert_hostname`, so this doesn't weaken certificate
checking.
"""

import socket
import ssl
import warnings
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv6Address, ip_address
from urllib.parse import urljoin, urlparse

import urllib3

# We deliberately skip certificate verification for the redirect-chain HEAD
# requests below (see safe_follow_redirects) — certificate validity is
# already checked independently by the ssl_certificate rule, and these
# requests never send or read anything sensitive. Silence the resulting
# per-request warning so it doesn't spam application logs.
warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)

CONNECT_TIMEOUT_SECONDS = 3
MAX_REDIRECTS = 5
ALLOWED_SCHEMES = {"http", "https"}
USER_AGENT = "CyberShield-URLScanner/1.0"


class UnsafeHostError(Exception):
    """Raised when a hostname resolves to a non-public / internal address."""


def is_public_ip(addr: IPv4Address | IPv6Address) -> bool:
    return not (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    )


def resolve_hostname(hostname: str) -> list[IPv4Address | IPv6Address]:
    """Resolve a hostname to all its IPs. Returns [] if resolution fails."""
    try:
        infos = socket.getaddrinfo(hostname, None)
    except (socket.gaierror, UnicodeError):
        return []

    addresses: list[IPv4Address | IPv6Address] = []
    for info in infos:
        raw_ip = info[4][0]
        try:
            addresses.append(ip_address(raw_ip.split("%")[0]))
        except ValueError:
            continue
    return addresses


def assert_safe_host(hostname: str, resolved_ips: list[IPv4Address | IPv6Address]) -> None:
    if not resolved_ips:
        raise UnsafeHostError(f"Could not resolve hostname: {hostname}")
    if not all(is_public_ip(addr) for addr in resolved_ips):
        raise UnsafeHostError(f"Hostname resolves to a non-public address: {hostname}")


def _resolve_and_validate(hostname: str) -> str:
    """Resolve + validate a hostname, returning one safe IP to connect to."""
    resolved = resolve_hostname(hostname)
    assert_safe_host(hostname, resolved)
    return str(resolved[0])


@dataclass
class RedirectHop:
    url: str
    status_code: int


@dataclass
class RedirectCheckResult:
    ok: bool
    hops: list[RedirectHop]
    final_url: str | None
    cross_domain: bool
    error: str | None = None


def _pinned_request(pinned_ip: str, hostname: str, scheme: str, port: int, path: str) -> urllib3.BaseHTTPResponse:
    """Issue a single HEAD request to `pinned_ip`, using `hostname` only for
    the Host header / TLS SNI — never for the actual DNS-resolved connection
    target. `redirect=False` so the caller controls redirect following (and
    re-validates the next hop) itself."""
    headers = {"Host": hostname, "User-Agent": USER_AGENT}

    if scheme == "https":
        pool = urllib3.HTTPSConnectionPool(
            pinned_ip,
            port=port,
            server_hostname=hostname,
            assert_hostname=hostname,
            cert_reqs="CERT_NONE",
            timeout=CONNECT_TIMEOUT_SECONDS,
            retries=False,
        )
    else:
        pool = urllib3.HTTPConnectionPool(
            pinned_ip, port=port, timeout=CONNECT_TIMEOUT_SECONDS, retries=False
        )

    try:
        return pool.request("HEAD", path, headers=headers, redirect=False, preload_content=False)
    finally:
        pool.close()


def safe_follow_redirects(url: str, hostname: str) -> RedirectCheckResult:
    """Follow redirects manually (not via automatic client redirect-following)
    so every hop's hostname can be resolved, validated, and pinned before
    it's connected to."""
    hops: list[RedirectHop] = []
    current_url = url
    original_hostname = hostname

    try:
        for _ in range(MAX_REDIRECTS + 1):
            parsed = urlparse(current_url)
            if parsed.scheme not in ALLOWED_SCHEMES:
                return RedirectCheckResult(False, hops, None, False, "Unsupported scheme in redirect chain.")

            current_hostname = parsed.hostname or ""
            pinned_ip = _resolve_and_validate(current_hostname)
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            path = urlparse(current_url)._replace(scheme="", netloc="").geturl() or "/"

            response = _pinned_request(pinned_ip, current_hostname, parsed.scheme, port, path)
            hops.append(RedirectHop(url=current_url, status_code=response.status))

            location = response.headers.get("Location")
            if response.status in (301, 302, 303, 307, 308) and location:
                current_url = urljoin(current_url, location)
                continue

            final_hostname = urlparse(current_url).hostname or ""
            return RedirectCheckResult(
                ok=True,
                hops=hops,
                final_url=current_url,
                cross_domain=final_hostname != original_hostname,
            )

        return RedirectCheckResult(False, hops, current_url, False, "Too many redirects.")
    except UnsafeHostError as exc:
        return RedirectCheckResult(False, hops, None, False, str(exc))
    except urllib3.exceptions.HTTPError as exc:
        return RedirectCheckResult(False, hops, None, False, f"Request failed: {exc}")


@dataclass
class CertificateInfo:
    status: str  # "valid" | "invalid" | "expired" | "unknown"
    detail: str | None = None
    not_after: str | None = None
    issuer: str | None = None
    # Sub-reason for status=="unknown", so "we couldn't check" (DNS failure,
    # timeout, connection refused) can be told apart from each other in the
    # scan report, without changing the (still-penalized) "unknown" status
    # or its score impact — see ssl_certificate.py.
    reason: str | None = None


def get_certificate_info(hostname: str, resolved_ips: list[IPv4Address | IPv6Address]) -> CertificateInfo:
    try:
        assert_safe_host(hostname, resolved_ips)
    except UnsafeHostError as exc:
        reason = "dns_unresolved" if not resolved_ips else "unsafe_host"
        return CertificateInfo(status="unknown", detail=str(exc), reason=reason)

    # Connect to the already-validated IP directly (never re-resolve the
    # hostname here) — `server_hostname` still drives SNI and the cert
    # hostname check, so this doesn't change what's actually verified.
    pinned_ip = str(resolved_ips[0])
    context = ssl.create_default_context()
    try:
        with socket.create_connection((pinned_ip, 443), timeout=CONNECT_TIMEOUT_SECONDS) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as tls_sock:
                cert = tls_sock.getpeercert()
    except ssl.SSLCertVerificationError as exc:
        reason = getattr(exc, "verify_message", "") or str(exc)
        if "expired" in reason.lower():
            return CertificateInfo(status="expired", detail=reason)
        return CertificateInfo(status="invalid", detail=reason)
    except (socket.timeout, TimeoutError) as exc:
        return CertificateInfo(status="unknown", detail=str(exc), reason="timeout")
    except ssl.SSLError as exc:
        return CertificateInfo(status="unknown", detail=str(exc), reason="ssl_error")
    except OSError as exc:
        return CertificateInfo(status="unknown", detail=str(exc), reason="connection_failed")

    issuer = dict(x[0] for x in cert.get("issuer", [])).get("organizationName")
    not_after = cert.get("notAfter")
    return CertificateInfo(status="valid", issuer=issuer, not_after=not_after)
