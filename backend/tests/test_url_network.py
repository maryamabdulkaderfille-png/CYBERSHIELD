import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from ipaddress import ip_address

import pytest

from app.services.url_scanner import network


def test_is_public_ip_rejects_private_ranges():
    assert not network.is_public_ip(ip_address("10.0.0.5"))
    assert not network.is_public_ip(ip_address("192.168.1.1"))
    assert not network.is_public_ip(ip_address("127.0.0.1"))
    assert not network.is_public_ip(ip_address("169.254.169.254"))  # cloud metadata endpoint
    assert not network.is_public_ip(ip_address("::1"))


def test_is_public_ip_accepts_public_addresses():
    assert network.is_public_ip(ip_address("93.184.216.34"))
    assert network.is_public_ip(ip_address("8.8.8.8"))


def test_resolve_hostname_returns_loopback_for_localhost():
    resolved = network.resolve_hostname("localhost")
    assert resolved
    assert all(addr.is_loopback for addr in resolved)


def test_resolve_hostname_returns_empty_for_unresolvable_host():
    assert network.resolve_hostname("this-host-does-not-exist.invalid") == []


def test_assert_safe_host_rejects_loopback():
    with pytest.raises(network.UnsafeHostError):
        network.assert_safe_host("localhost", network.resolve_hostname("localhost"))


def test_assert_safe_host_rejects_empty_resolution():
    with pytest.raises(network.UnsafeHostError):
        network.assert_safe_host("nowhere.invalid", [])


def test_safe_follow_redirects_refuses_real_unsafe_host():
    """No monkeypatching: proves the guard actually blocks a real hostname
    that resolves to loopback, end to end."""
    result = network.safe_follow_redirects("http://localhost:1/some-path", "localhost")
    assert result.ok is False
    assert result.error is not None


def test_get_certificate_info_unknown_for_unsafe_host():
    info = network.get_certificate_info("localhost", network.resolve_hostname("localhost"))
    assert info.status == "unknown"
    assert info.reason == "unsafe_host"


def test_get_certificate_info_unknown_reason_for_dns_failure():
    """Distinguishes 'couldn't resolve the hostname at all' from the
    'resolved somewhere unsafe' case above — both are status=='unknown'
    (same score impact) but should be tellable apart in the report."""
    info = network.get_certificate_info("this-host-does-not-exist.invalid", [])
    assert info.status == "unknown"
    assert info.reason == "dns_unresolved"


class _RedirectingHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        if self.path == "/start":
            self.send_response(302)
            self.send_header("Location", "/final")
            self.end_headers()
        else:
            self.send_response(200)
            self.end_headers()

    def log_message(self, format, *args):  # noqa: A002 - silence test server logging
        pass


@pytest.fixture()
def local_http_server():
    server = HTTPServer(("127.0.0.1", 0), _RedirectingHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    thread.join(timeout=2)


def test_safe_follow_redirects_follows_and_pins_to_validated_ip(local_http_server, monkeypatch):
    """Bypasses the SSRF guard deliberately (loopback would otherwise be
    blocked) to prove the actual redirect-following/IP-pinning logic works:
    it follows the 302 to /final and stops there."""
    port = local_http_server.server_address[1]

    monkeypatch.setattr(network, "resolve_hostname", lambda hostname: [ip_address("127.0.0.1")])
    monkeypatch.setattr(network, "is_public_ip", lambda addr: True)

    result = network.safe_follow_redirects(f"http://test.local:{port}/start", "test.local")

    assert result.ok is True
    assert len(result.hops) == 2
    assert result.hops[0].status_code == 302
    assert result.hops[1].status_code == 200
    assert result.final_url == f"http://test.local:{port}/final"
    assert result.cross_domain is False


def test_safe_follow_redirects_detects_cross_domain(local_http_server, monkeypatch):
    port = local_http_server.server_address[1]

    monkeypatch.setattr(network, "resolve_hostname", lambda hostname: [ip_address("127.0.0.1")])
    monkeypatch.setattr(network, "is_public_ip", lambda addr: True)

    result = network.safe_follow_redirects(f"http://test.local:{port}/start", "a-different-original-host.local")

    assert result.ok is True
    assert result.cross_domain is True
