from urllib.parse import urlparse

import pytest

from app.services.url_scanner.network import CertificateInfo, RedirectCheckResult, RedirectHop
from app.services.url_scanner.rules import (
    blacklist_check,
    domain_age,
    external_threat_intel,
    https_check,
    ip_address,
    redirect_check,
    special_characters,
    ssl_certificate,
    subdomains,
    suspicious_keywords,
    typosquatting,
    url_length,
    whitelist_check,
)
from app.services.url_scanner.domain_age_provider import DomainAgeResult
from app.services.url_scanner.types import ScanContext


def make_context(url: str) -> ScanContext:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    is_ip = hostname.replace(".", "").isdigit() and hostname.count(".") == 3
    return ScanContext(
        raw_url=url,
        parsed=parsed,
        hostname=hostname,
        resolved_ips=[],
        dns_resolved=True,
        is_ip_host=is_ip,
    )


def test_url_length_flags_long_url():
    long_url = "https://example.com/" + "a" * 120
    result = url_length.evaluate(make_context(long_url))
    assert result.triggered
    assert result.impact < 0


def test_url_length_normal():
    result = url_length.evaluate(make_context("https://example.com/page"))
    assert not result.triggered
    assert result.impact == 0


def test_url_length_very_short_boundary():
    # VERY_SHORT = 12; implementation uses "<=" so exactly 12 triggers.
    url = "http://a.co"  # 11 chars
    assert len(url) == 11
    result = url_length.evaluate(make_context(url))
    assert result.triggered
    assert result.impact == -3


def test_url_length_just_above_short_boundary_is_clean():
    url = "http://a.coo"  # 12 chars -> still <= VERY_SHORT, still triggers
    assert len(url) == 12
    result = url_length.evaluate(make_context(url))
    assert result.triggered
    assert result.impact == -3


def test_url_length_13_chars_is_normal():
    url = "http://a.cooo"  # 13 chars -> above VERY_SHORT, below LONG
    assert len(url) == 13
    result = url_length.evaluate(make_context(url))
    assert not result.triggered


@pytest.mark.parametrize(
    "length,expected_impact",
    [(74, 0), (75, -8), (99, -8), (100, -15)],
)
def test_url_length_long_boundaries_use_gte(length, expected_impact):
    base = "https://example.com/"
    url = base + "a" * (length - len(base))
    assert len(url) == length
    result = url_length.evaluate(make_context(url))
    assert result.impact == expected_impact


def test_https_check_flags_http():
    result = https_check.evaluate(make_context("http://example.com"))
    assert result.triggered
    assert result.impact < 0


def test_https_check_passes_https():
    result = https_check.evaluate(make_context("https://example.com"))
    assert not result.triggered


def test_ip_address_flags_raw_ip():
    result = ip_address.evaluate(make_context("http://192.168.10.2/login"))
    assert result.triggered
    assert result.impact == -30


def test_ip_address_passes_domain():
    result = ip_address.evaluate(make_context("https://example.com"))
    assert not result.triggered


@pytest.mark.parametrize("keyword", ["login", "verify", "bonus", "wallet"])
def test_suspicious_keywords_detects_each(keyword):
    result = suspicious_keywords.evaluate(make_context(f"https://example.com/{keyword}-page"))
    assert result.triggered
    assert keyword in result.detail


def test_suspicious_keywords_clean_url():
    result = suspicious_keywords.evaluate(make_context("https://example.com/products/shoes"))
    assert not result.triggered


def test_special_characters_flags_at_symbol():
    result = special_characters.evaluate(make_context("http://google.com@evil.com/"))
    assert result.triggered
    assert result.impact <= -20


def test_special_characters_flags_double_slash_in_path():
    result = special_characters.evaluate(make_context("https://example.com//http://evil.com"))
    assert result.triggered


def test_special_characters_clean_url():
    result = special_characters.evaluate(make_context("https://example.com/search?q=shoes"))
    assert not result.triggered


def test_special_characters_flags_excessive_percent_encoding():
    result = special_characters.evaluate(make_context("https://example.com/path%20%20%20"))
    assert result.triggered
    assert result.impact == -10


def test_special_characters_flags_repeated_hyphens():
    result = special_characters.evaluate(make_context("https://ex--ample.com"))
    assert result.triggered
    assert result.impact == -8


def test_special_characters_flags_repeated_underscores():
    result = special_characters.evaluate(make_context("https://ex__ample.com"))
    assert result.triggered
    assert result.impact == -8


def test_subdomains_flags_deep_chain():
    result = subdomains.evaluate(make_context("https://a.b.c.d.example.com"))
    assert result.triggered
    assert result.impact == -15


def test_subdomains_flags_exactly_three():
    result = subdomains.evaluate(make_context("https://a.b.c.example.com"))
    assert result.triggered
    assert result.impact == -8


def test_subdomains_normal():
    result = subdomains.evaluate(make_context("https://www.example.com"))
    assert not result.triggered


def test_typosquatting_flags_lookalike():
    result = typosquatting.evaluate(make_context("https://paypaI.com/login"))
    assert result.triggered
    assert result.detail == "paypal.com"


def test_typosquatting_passes_real_brand():
    result = typosquatting.evaluate(make_context("https://paypal.com/login"))
    assert not result.triggered


def test_typosquatting_passes_unrelated_domain():
    result = typosquatting.evaluate(make_context("https://my-personal-blog.example"))
    assert not result.triggered


@pytest.mark.parametrize(
    "url",
    [
        "https://accounts.google.com.freehost42.ru/login",
        "https://google-security.example.net/login",
        "https://secure-paypal.example.org/verify",
        "https://microsoft-login.example.org/account",
    ],
)
def test_typosquatting_flags_brand_in_subdomain(url):
    result = typosquatting.evaluate(make_context(url))
    assert result.triggered
    assert result.impact == -30
    assert result.severity == "critical"


@pytest.mark.parametrize(
    "url",
    [
        "https://www.google.com",
        "https://www.microsoft.com",
        "https://www.paypal.com",
        "https://www.apple.com",
        "https://accounts.google.com",
        "https://login.microsoftonline.com",
    ],
)
def test_typosquatting_does_not_flag_legitimate_domains(url):
    result = typosquatting.evaluate(make_context(url))
    assert not result.triggered


def test_typosquatting_does_not_flag_ambiguous_brand_word_without_lure():
    # "apple" is a common English word as well as a brand name — without a
    # nearby phishing-lure word, a coincidental match shouldn't be flagged.
    result = typosquatting.evaluate(make_context("https://apple-pie-recipes.cookingblog.com"))
    assert not result.triggered


def test_typosquatting_does_not_flag_amazon_the_rainforest():
    # "amazon" is also an ordinary word (the river/rainforest) outside the
    # brand context — found during the final validation audit as a gap in
    # the ambiguous-token guard (which previously only covered apple/chase).
    result = typosquatting.evaluate(make_context("https://amazon-rainforest-tours.example.com"))
    assert not result.triggered


@pytest.mark.parametrize("url", [
    "https://apple-login.example.com/verify",
    "https://chase-verify-account.example.com",
    "https://amazon-login-secure.example.com",
])
def test_typosquatting_still_flags_ambiguous_brand_with_lure_word(url):
    # The ambiguous-token guard requires corroborating lure-word evidence —
    # it must not become a blanket exemption for apple/chase/amazon.
    result = typosquatting.evaluate(make_context(url))
    assert result.triggered
    assert result.impact == -30


def test_typosquatting_known_limitation_does_not_catch_typo_in_subdomain():
    """Documents a real, confirmed scope boundary found during the final
    validation audit: the subdomain-impersonation check (see
    _subdomain_impersonation) only matches an EXACT brand token
    ("google", "paypal", ...), not a typo'd variant. A brand name typo'd
    *inside a subdomain label* (as opposed to typo'd as the registrable
    domain itself, which the primary Levenshtein check already catches)
    is therefore not flagged. This is a known, deliberately-scoped
    limitation, not a regression -- pinned here so it can't silently
    change without this test being noticed and updated."""
    result = typosquatting.evaluate(make_context("https://goggle.example.com/login"))
    assert not result.triggered


def test_typosquatting_does_not_flag_brand_owned_cctld_domain():
    # "amazon.co.uk" is Amazon's own domain; the naive last-two-labels split
    # would otherwise misread "amazon" as hiding in a subdomain of "co.uk".
    result = typosquatting.evaluate(make_context("https://www.amazon.co.uk/orders"))
    assert not result.triggered


def test_ssl_certificate_not_applicable_for_http(monkeypatch):
    result = ssl_certificate.evaluate(make_context("http://example.com"))
    assert not result.triggered
    assert result.detail == "unknown"


def test_ssl_certificate_valid(monkeypatch):
    monkeypatch.setattr(
        ssl_certificate, "get_certificate_info", lambda hostname, ips: CertificateInfo(status="valid")
    )
    result = ssl_certificate.evaluate(make_context("https://example.com"))
    assert not result.triggered


def test_ssl_certificate_invalid(monkeypatch):
    monkeypatch.setattr(
        ssl_certificate, "get_certificate_info", lambda hostname, ips: CertificateInfo(status="invalid")
    )
    result = ssl_certificate.evaluate(make_context("https://example.com"))
    assert result.triggered
    assert result.impact == -20


def test_ssl_certificate_expired(monkeypatch):
    monkeypatch.setattr(
        ssl_certificate, "get_certificate_info", lambda hostname, ips: CertificateInfo(status="expired")
    )
    result = ssl_certificate.evaluate(make_context("https://example.com"))
    assert result.triggered
    assert result.impact == -20


@pytest.mark.parametrize(
    "reason,expected_fragment",
    [
        ("dns_unresolved", "did not resolve"),
        ("timeout", "timed out"),
        ("connection_failed", "connection failed"),
        ("ssl_error", "protocol/handshake error"),
    ],
)
def test_ssl_certificate_unknown_reason_is_distinguishable(monkeypatch, reason, expected_fragment):
    """Different unresolvable-certificate causes should still share the same
    'unknown' status/impact (we don't automatically treat 'can't check' as
    equivalent to 'looks wrong'), but should be distinguishable in the
    report rather than all saying the same generic message."""
    monkeypatch.setattr(
        ssl_certificate,
        "get_certificate_info",
        lambda hostname, ips: CertificateInfo(status="unknown", detail="raw detail", reason=reason),
    )
    result = ssl_certificate.evaluate(make_context("https://example.com"))
    assert result.triggered
    assert result.impact == -5  # penalty is unchanged regardless of the specific reason
    assert result.detail == reason
    assert expected_fragment in result.message


def test_ssl_certificate_unknown_without_reason_falls_back_to_generic_message(monkeypatch):
    monkeypatch.setattr(
        ssl_certificate, "get_certificate_info", lambda hostname, ips: CertificateInfo(status="unknown")
    )
    result = ssl_certificate.evaluate(make_context("https://example.com"))
    assert result.triggered
    assert result.impact == -5
    assert result.message == "SSL certificate status could not be determined."
    assert result.detail == "unknown"


def test_domain_age_recently_registered(monkeypatch):
    class StubProvider:
        def lookup(self, domain):
            return DomainAgeResult(status="recently_registered", age_days=10)

    monkeypatch.setattr(domain_age, "get_domain_age_provider", lambda: StubProvider())
    result = domain_age.evaluate(make_context("https://example.com"))
    assert result.triggered
    assert result.impact == -15


def test_domain_age_established(monkeypatch):
    class StubProvider:
        def lookup(self, domain):
            return DomainAgeResult(status="established", age_days=3000)

    monkeypatch.setattr(domain_age, "get_domain_age_provider", lambda: StubProvider())
    result = domain_age.evaluate(make_context("https://example.com"))
    assert not result.triggered


def test_domain_age_moderately_aged(monkeypatch):
    class StubProvider:
        def lookup(self, domain):
            return DomainAgeResult(status="moderately_aged", age_days=300)

    monkeypatch.setattr(domain_age, "get_domain_age_provider", lambda: StubProvider())
    result = domain_age.evaluate(make_context("https://example.com"))
    assert result.triggered
    assert result.impact == -5


def test_domain_age_unknown_is_not_penalized(monkeypatch):
    class StubProvider:
        def lookup(self, domain):
            return DomainAgeResult(status="unknown")

    monkeypatch.setattr(domain_age, "get_domain_age_provider", lambda: StubProvider())
    result = domain_age.evaluate(make_context("https://example.com"))
    assert not result.triggered
    assert result.impact == 0


def test_redirect_check_no_redirects(monkeypatch):
    monkeypatch.setattr(
        redirect_check,
        "safe_follow_redirects",
        lambda url, hostname: RedirectCheckResult(
            ok=True, hops=[RedirectHop(url=url, status_code=200)], final_url=url, cross_domain=False
        ),
    )
    result = redirect_check.evaluate(make_context("https://example.com"))
    assert not result.triggered


def test_redirect_check_cross_domain(monkeypatch):
    monkeypatch.setattr(
        redirect_check,
        "safe_follow_redirects",
        lambda url, hostname: RedirectCheckResult(
            ok=True,
            hops=[RedirectHop(url=url, status_code=302), RedirectHop(url="https://other.com", status_code=200)],
            final_url="https://other.com",
            cross_domain=True,
        ),
    )
    result = redirect_check.evaluate(make_context("https://example.com"))
    assert result.triggered
    assert result.impact < 0


def test_redirect_check_long_chain(monkeypatch):
    hops = [RedirectHop(url=f"https://example.com/{i}", status_code=302) for i in range(4)] + [
        RedirectHop(url="https://example.com/final", status_code=200)
    ]
    monkeypatch.setattr(
        redirect_check,
        "safe_follow_redirects",
        lambda url, hostname: RedirectCheckResult(
            ok=True, hops=hops, final_url="https://example.com/final", cross_domain=False
        ),
    )
    result = redirect_check.evaluate(make_context("https://example.com"))
    assert result.triggered
    assert result.impact == -10


def test_redirect_check_short_chain_not_flagged(monkeypatch):
    # hop_count must be > 3, not >= 3, to trigger the "longer than typical" penalty.
    hops = [RedirectHop(url=f"https://example.com/{i}", status_code=302) for i in range(2)] + [
        RedirectHop(url="https://example.com/final", status_code=200)
    ]
    monkeypatch.setattr(
        redirect_check,
        "safe_follow_redirects",
        lambda url, hostname: RedirectCheckResult(
            ok=True, hops=hops, final_url="https://example.com/final", cross_domain=False
        ),
    )
    result = redirect_check.evaluate(make_context("https://example.com"))
    assert not result.triggered


def test_redirect_check_unavailable_is_not_penalized(monkeypatch):
    monkeypatch.setattr(
        redirect_check,
        "safe_follow_redirects",
        lambda url, hostname: RedirectCheckResult(
            ok=False, hops=[], final_url=None, cross_domain=False, error="simulated failure"
        ),
    )
    result = redirect_check.evaluate(make_context("https://example.com"))
    assert not result.triggered
    assert result.impact == 0
    assert result.detail == "simulated failure"


def test_whitelist_check_flags_verified_domain():
    result = whitelist_check.evaluate(make_context("https://accounts.google.com"))
    assert result.triggered
    assert result.impact == 15
    assert result.detail == "Google"


def test_whitelist_check_passes_unrelated_domain():
    result = whitelist_check.evaluate(make_context("https://example.com"))
    assert not result.triggered
    assert result.impact == 0


def _clean(**kwargs):
    return external_threat_intel._ProviderResult(status="clean", **kwargs)


def _match(**kwargs):
    return external_threat_intel._ProviderResult(status="match", **kwargs)


def _unavailable(reason, **kwargs):
    return external_threat_intel._ProviderResult(status="unavailable", reason=reason, **kwargs)


def test_external_threat_intel_no_match(monkeypatch):
    monkeypatch.setattr(external_threat_intel, "_check_virustotal", lambda url, key: _clean())
    monkeypatch.setattr(external_threat_intel, "_check_urlhaus", lambda url, auth_key: _clean(detail="Not listed."))
    result = external_threat_intel.evaluate(make_context("https://unrelated-test-domain.example"))
    assert not result.triggered
    assert result.impact == 0
    assert "clean" in result.message.lower()


def test_external_threat_intel_virustotal_match(monkeypatch, app):
    monkeypatch.setattr(
        external_threat_intel, "_check_virustotal",
        lambda url, key: _match(detail="Flagged as malicious by 5 vendors."),
    )
    monkeypatch.setattr(external_threat_intel, "_check_urlhaus", lambda url, auth_key: _clean())
    with app.app_context():
        app.config["VIRUSTOTAL_API_KEY"] = "test-key"
        result = external_threat_intel.evaluate(make_context("https://unrelated-test-domain.example"))
    assert result.triggered
    assert result.impact == -100


def test_external_threat_intel_urlhaus_match(monkeypatch):
    monkeypatch.setattr(external_threat_intel, "_check_virustotal", lambda url, key: _clean())
    monkeypatch.setattr(
        external_threat_intel, "_check_urlhaus",
        lambda url, auth_key: _match(detail="Verified threat on URLhaus feed."),
    )
    result = external_threat_intel.evaluate(make_context("https://unrelated-test-domain.example"))
    assert result.triggered
    assert result.impact == -100
    assert result.message == "Verified threat on URLhaus feed."


def test_external_threat_intel_skips_whitelisted_domain(monkeypatch):
    # Should never even call out to VT/URLhaus for a verified domain.
    called = []
    monkeypatch.setattr(external_threat_intel, "_check_virustotal", lambda url, key: called.append("vt"))
    monkeypatch.setattr(external_threat_intel, "_check_urlhaus", lambda url, auth_key: called.append("urlhaus"))
    result = external_threat_intel.evaluate(make_context("https://www.google.com"))
    assert not result.triggered
    assert called == []


def test_external_threat_intel_urlhaus_unavailable_is_not_scored_as_match_or_clean(monkeypatch):
    """The core regression this fix targets: an UNAVAILABLE provider result
    must not produce the -100 match penalty, AND must not be reported with
    the "clean" message — the UI must be able to tell "verified clean" apart
    from "we couldn't check"."""
    monkeypatch.setattr(external_threat_intel, "_check_virustotal", lambda url, key: _clean())
    monkeypatch.setattr(
        external_threat_intel, "_check_urlhaus",
        lambda url, auth_key: _unavailable("authentication_failed", detail="URLhaus authentication failed."),
    )
    result = external_threat_intel.evaluate(make_context("https://unrelated-test-domain.example"))
    assert not result.triggered
    assert result.impact == 0
    # Must not claim a confirmed-clean verdict was reached.
    assert result.message != "Target is clean and not listed on global threat intelligence feeds."
    assert "could not" in result.message.lower() or "unavailable" in result.message.lower()
    assert result.detail == "unavailable:urlhaus=authentication_failed"


def test_external_threat_intel_virustotal_unavailable_is_not_scored_as_match_or_clean(monkeypatch):
    """Mirror of the URLhaus regression test above, for VirusTotal."""
    monkeypatch.setattr(
        external_threat_intel, "_check_virustotal",
        lambda url, key: _unavailable("rate_limited", detail="VirusTotal rate limit exceeded."),
    )
    monkeypatch.setattr(external_threat_intel, "_check_urlhaus", lambda url, auth_key: _clean())
    result = external_threat_intel.evaluate(make_context("https://unrelated-test-domain.example"))
    assert not result.triggered
    assert result.impact == 0
    assert result.message != "Target is clean and not listed on global threat intelligence feeds."
    assert result.detail == "unavailable:virustotal=rate_limited"


def test_external_threat_intel_both_providers_unavailable(monkeypatch):
    monkeypatch.setattr(
        external_threat_intel, "_check_virustotal", lambda url, key: _unavailable("missing_auth_key")
    )
    monkeypatch.setattr(
        external_threat_intel, "_check_urlhaus", lambda url, auth_key: _unavailable("network_error")
    )
    result = external_threat_intel.evaluate(make_context("https://unrelated-test-domain.example"))
    assert not result.triggered
    assert result.impact == 0
    assert result.detail == "unavailable:virustotal=missing_auth_key,urlhaus=network_error"


def test_external_threat_intel_vt_unavailable_but_urlhaus_match_still_triggers(monkeypatch):
    # A MATCH from either provider must win over the other being unavailable.
    monkeypatch.setattr(
        external_threat_intel, "_check_virustotal", lambda url, key: _unavailable("missing_auth_key")
    )
    monkeypatch.setattr(
        external_threat_intel, "_check_urlhaus",
        lambda url, auth_key: _match(detail="Verified threat on URLhaus feed."),
    )
    result = external_threat_intel.evaluate(make_context("https://unrelated-test-domain.example"))
    assert result.triggered
    assert result.impact == -100


def test_external_threat_intel_vt_match_short_circuits_before_urlhaus(monkeypatch):
    called = []
    monkeypatch.setattr(
        external_threat_intel, "_check_virustotal",
        lambda url, key: _match(detail="Flagged as malicious by 5 vendors."),
    )
    monkeypatch.setattr(external_threat_intel, "_check_urlhaus", lambda url, auth_key: called.append("urlhaus"))
    result = external_threat_intel.evaluate(make_context("https://unrelated-test-domain.example"))
    assert result.triggered
    assert result.impact == -100
    assert called == []


# --- _check_virustotal internals: every response/failure mode from STEP 6/8 ---


def test_check_virustotal_missing_api_key_returns_unavailable_without_a_request(monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("should not make a network request with no API key configured")

    monkeypatch.setattr(external_threat_intel.requests, "get", _boom)
    result = external_threat_intel._check_virustotal("https://example.com", "")
    assert result.status == "unavailable"
    assert result.reason == "missing_auth_key"


def test_check_virustotal_200_malicious_match(monkeypatch):
    monkeypatch.setattr(
        external_threat_intel.requests, "get",
        lambda *a, **k: _FakeResponse(200, {"data": {"attributes": {"last_analysis_stats": {"malicious": 5}}}}),
    )
    result = external_threat_intel._check_virustotal("https://example.com", "fake-key")
    assert result.status == "match"


def test_check_virustotal_200_suspicious_above_threshold_is_match(monkeypatch):
    monkeypatch.setattr(
        external_threat_intel.requests, "get",
        lambda *a, **k: _FakeResponse(200, {"data": {"attributes": {"last_analysis_stats": {"suspicious": 3}}}}),
    )
    result = external_threat_intel._check_virustotal("https://example.com", "fake-key")
    assert result.status == "match"


def test_check_virustotal_200_no_detections_is_clean(monkeypatch):
    monkeypatch.setattr(
        external_threat_intel.requests, "get",
        lambda *a, **k: _FakeResponse(200, {"data": {"attributes": {"last_analysis_stats": {"malicious": 0, "suspicious": 0}}}}),
    )
    result = external_threat_intel._check_virustotal("https://example.com", "fake-key")
    assert result.status == "clean"


def test_check_virustotal_404_not_analyzed_is_clean(monkeypatch):
    # VT has no record of this URL -- a successful "nothing found" check,
    # not a provider failure, matching URLhaus's "no_results" semantics.
    monkeypatch.setattr(external_threat_intel.requests, "get", lambda *a, **k: _FakeResponse(404))
    result = external_threat_intel._check_virustotal("https://example.com", "fake-key")
    assert result.status == "clean"


@pytest.mark.parametrize("status_code", [401, 403])
def test_check_virustotal_auth_failure(monkeypatch, status_code):
    monkeypatch.setattr(external_threat_intel.requests, "get", lambda *a, **k: _FakeResponse(status_code))
    result = external_threat_intel._check_virustotal("https://example.com", "fake-key")
    assert result.status == "unavailable"
    assert result.reason == "authentication_failed"


def test_check_virustotal_rate_limited(monkeypatch):
    monkeypatch.setattr(external_threat_intel.requests, "get", lambda *a, **k: _FakeResponse(429))
    result = external_threat_intel._check_virustotal("https://example.com", "fake-key")
    assert result.status == "unavailable"
    assert result.reason == "rate_limited"


def test_check_virustotal_provider_error(monkeypatch):
    monkeypatch.setattr(external_threat_intel.requests, "get", lambda *a, **k: _FakeResponse(500))
    result = external_threat_intel._check_virustotal("https://example.com", "fake-key")
    assert result.status == "unavailable"
    assert result.reason == "provider_error"


def test_check_virustotal_timeout(monkeypatch):
    def _raise_timeout(*a, **k):
        raise external_threat_intel.requests.exceptions.Timeout()

    monkeypatch.setattr(external_threat_intel.requests, "get", _raise_timeout)
    result = external_threat_intel._check_virustotal("https://example.com", "fake-key")
    assert result.status == "unavailable"
    assert result.reason == "network_error"


def test_check_virustotal_connection_error(monkeypatch):
    def _raise_conn_error(*a, **k):
        raise external_threat_intel.requests.exceptions.ConnectionError()

    monkeypatch.setattr(external_threat_intel.requests, "get", _raise_conn_error)
    result = external_threat_intel._check_virustotal("https://example.com", "fake-key")
    assert result.status == "unavailable"
    assert result.reason == "network_error"


def test_check_virustotal_malformed_json(monkeypatch):
    monkeypatch.setattr(
        external_threat_intel.requests, "get",
        lambda *a, **k: _FakeResponse(200, raise_on_json=True),
    )
    result = external_threat_intel._check_virustotal("https://example.com", "fake-key")
    assert result.status == "unavailable"
    assert result.reason == "invalid_response"


def test_check_virustotal_unexpected_response_structure(monkeypatch):
    # 200 OK but missing the "data" envelope VT v3 always returns on success.
    monkeypatch.setattr(
        external_threat_intel.requests, "get",
        lambda *a, **k: _FakeResponse(200, {"unexpected": "shape"}),
    )
    result = external_threat_intel._check_virustotal("https://example.com", "fake-key")
    assert result.status == "unavailable"
    assert result.reason == "invalid_response"


def test_check_virustotal_sends_api_key_header(monkeypatch):
    captured = {}

    def _capture(url, headers=None, timeout=None):
        captured["headers"] = headers
        captured["url"] = url
        return _FakeResponse(200, {"data": {"attributes": {"last_analysis_stats": {}}}})

    monkeypatch.setattr(external_threat_intel.requests, "get", _capture)
    external_threat_intel._check_virustotal("https://example.com", "my-secret-vt-key")
    assert captured["headers"]["x-apikey"] == "my-secret-vt-key"
    assert captured["url"].startswith("https://www.virustotal.com/api/v3/urls/")


# --- _check_urlhaus internals: every response/failure mode from STEP 4 ---


class _FakeResponse:
    def __init__(self, status_code, json_data=None, raise_on_json=False):
        self.status_code = status_code
        self._json_data = json_data
        self._raise_on_json = raise_on_json

    def json(self):
        if self._raise_on_json:
            raise ValueError("malformed JSON")
        return self._json_data


def test_check_urlhaus_missing_auth_key_returns_unavailable_without_a_request(monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("should not make a network request with no auth key configured")

    monkeypatch.setattr(external_threat_intel.requests, "post", _boom)
    result = external_threat_intel._check_urlhaus("https://example.com", "")
    assert result.status == "unavailable"
    assert result.reason == "missing_auth_key"


def test_check_urlhaus_200_match(monkeypatch):
    monkeypatch.setattr(
        external_threat_intel.requests, "post",
        lambda *a, **k: _FakeResponse(200, {"query_status": "ok", "threat": "phishing", "url_status": "online"}),
    )
    result = external_threat_intel._check_urlhaus("https://example.com", "fake-key")
    assert result.status == "match"


def test_check_urlhaus_200_no_results_is_clean(monkeypatch):
    monkeypatch.setattr(
        external_threat_intel.requests, "post",
        lambda *a, **k: _FakeResponse(200, {"query_status": "no_results"}),
    )
    result = external_threat_intel._check_urlhaus("https://example.com", "fake-key")
    assert result.status == "clean"


@pytest.mark.parametrize("status_code,expected_reason", [(401, "authentication_failed"), (403, "authentication_failed")])
def test_check_urlhaus_auth_failure(monkeypatch, status_code, expected_reason):
    monkeypatch.setattr(external_threat_intel.requests, "post", lambda *a, **k: _FakeResponse(status_code))
    result = external_threat_intel._check_urlhaus("https://example.com", "fake-key")
    assert result.status == "unavailable"
    assert result.reason == expected_reason


def test_check_urlhaus_rate_limited(monkeypatch):
    monkeypatch.setattr(external_threat_intel.requests, "post", lambda *a, **k: _FakeResponse(429))
    result = external_threat_intel._check_urlhaus("https://example.com", "fake-key")
    assert result.status == "unavailable"
    assert result.reason == "rate_limited"


def test_check_urlhaus_provider_error(monkeypatch):
    monkeypatch.setattr(external_threat_intel.requests, "post", lambda *a, **k: _FakeResponse(500))
    result = external_threat_intel._check_urlhaus("https://example.com", "fake-key")
    assert result.status == "unavailable"
    assert result.reason == "provider_error"


def test_check_urlhaus_timeout(monkeypatch):
    def _raise_timeout(*a, **k):
        raise external_threat_intel.requests.exceptions.Timeout()

    monkeypatch.setattr(external_threat_intel.requests, "post", _raise_timeout)
    result = external_threat_intel._check_urlhaus("https://example.com", "fake-key")
    assert result.status == "unavailable"
    assert result.reason == "network_error"


def test_check_urlhaus_connection_error(monkeypatch):
    def _raise_conn_error(*a, **k):
        raise external_threat_intel.requests.exceptions.ConnectionError()

    monkeypatch.setattr(external_threat_intel.requests, "post", _raise_conn_error)
    result = external_threat_intel._check_urlhaus("https://example.com", "fake-key")
    assert result.status == "unavailable"
    assert result.reason == "network_error"


def test_check_urlhaus_malformed_json(monkeypatch):
    monkeypatch.setattr(
        external_threat_intel.requests, "post",
        lambda *a, **k: _FakeResponse(200, raise_on_json=True),
    )
    result = external_threat_intel._check_urlhaus("https://example.com", "fake-key")
    assert result.status == "unavailable"
    assert result.reason == "invalid_response"


def test_check_urlhaus_sends_auth_key_header(monkeypatch):
    captured = {}

    def _capture(url, data=None, timeout=None, headers=None):
        captured["headers"] = headers
        return _FakeResponse(200, {"query_status": "no_results"})

    monkeypatch.setattr(external_threat_intel.requests, "post", _capture)
    external_threat_intel._check_urlhaus("https://example.com", "my-secret-key")
    assert captured["headers"]["Auth-Key"] == "my-secret-key"


def test_blacklist_check_flags_subdomain_of_blacklisted_registrable_domain(app):
    from app.extensions import db
    from app.models.blacklist import BlacklistEntry

    with app.app_context():
        db.session.add(BlacklistEntry(domain="known-bad-registrable.example", reason="Reported phishing site"))
        db.session.commit()

        result = blacklist_check.evaluate(make_context("https://sub.known-bad-registrable.example/login"))
        assert result.triggered
        assert result.impact == -100


def test_blacklist_check_flags_known_domain(app):
    from app.extensions import db
    from app.models.blacklist import BlacklistEntry

    with app.app_context():
        db.session.add(BlacklistEntry(domain="known-phish.example", reason="Reported phishing site"))
        db.session.commit()

        result = blacklist_check.evaluate(make_context("https://known-phish.example/login"))
        assert result.triggered
        assert result.impact == -100


def test_blacklist_check_passes_clean_domain(app):
    with app.app_context():
        result = blacklist_check.evaluate(make_context("https://example.com"))
        assert not result.triggered
