import time

import pytest

from app.services.url_scanner import engine
from app.services.url_scanner.engine import quick_classify, scan_url
from app.services.url_scanner.rules import external_threat_intel, redirect_check, ssl_certificate
from app.services.url_scanner.types import RiskLevel, RuleResult
from app.utils.errors import APIError


def test_scan_url_rejects_private_ip_literal(app):
    with app.app_context():
        with pytest.raises(APIError) as exc_info:
            scan_url("http://192.168.1.10/")
        assert exc_info.value.status_code == 422


def test_scan_url_rejects_loopback_hostname(app):
    with app.app_context():
        with pytest.raises(APIError) as exc_info:
            scan_url("http://localhost:5173/dashboard")
        assert exc_info.value.status_code == 422


def test_quick_classify_still_scores_private_ip_links(app):
    """Unlike scan_url, quick_classify (used to score links embedded in
    emails) must keep scoring a raw-private-IP link via the ip_address rule
    rather than raising — a phishing email linking to one is still a real
    signal worth flagging, not a target CyberShield itself is connecting to."""
    with app.app_context():
        score, risk = quick_classify("http://192.168.1.10/phish-login")
        assert risk in {RiskLevel.SUSPICIOUS, RiskLevel.DANGEROUS}


def test_clean_https_url_scores_high(app):
    with app.app_context():
        report = scan_url("https://example.com/about")
        assert report.trust_score >= 90
        assert report.risk_level == RiskLevel.SAFE
        assert report.reasons == []


def test_ip_and_keyword_and_no_https_scores_low(app):
    with app.app_context():
        # A public IP — a private/internal one would now be rejected outright
        # by the private-target guard tested separately (see test_url_network.py).
        report = scan_url("http://8.8.8.8/login-verify-account")
        assert report.trust_score < 40
        assert report.risk_level == RiskLevel.DANGEROUS
        assert any("IP address" in reason for reason in report.reasons)
        assert len(report.recommendations) > 0


def test_typosquat_url_is_flagged_critical(app):
    with app.app_context():
        report = scan_url("https://paypaI.com/signin")
        assert report.risk_level in {RiskLevel.SUSPICIOUS, RiskLevel.DANGEROUS}
        assert any("typosquatting" in reason.lower() for reason in report.reasons)


def test_score_never_goes_below_zero_or_above_hundred(app):
    with app.app_context():
        report = scan_url("http://8.8.4.4/login-verify-secure-bank-wallet-paypal-password")
        assert 0 <= report.trust_score <= 100


def test_slow_network_rule_times_out_gracefully(app, monkeypatch):
    """One hanging network-bound rule shouldn't block the whole scan past
    the engine's timeout budget, and shouldn't affect the score."""
    monkeypatch.setattr(engine, "NETWORK_RULES_TIMEOUT_SECONDS", 1)

    def _hang(ctx):
        time.sleep(5)
        raise AssertionError("should have been abandoned by the engine's timeout")

    monkeypatch.setattr(ssl_certificate, "evaluate", _hang)

    with app.app_context():
        start = time.monotonic()
        report = scan_url("https://example.com")
        elapsed = time.monotonic() - start

    assert elapsed < 3
    ssl_result = next(r for r in report.rule_results if r.rule == "ssl_certificate")
    assert ssl_result.detail == "timeout"
    assert ssl_result.impact == 0


def test_network_rule_exception_is_contained(app, monkeypatch):
    """A bug in one rule shouldn't take the whole scan down."""

    def _boom(ctx):
        raise RuntimeError("simulated rule bug")

    monkeypatch.setattr(redirect_check, "evaluate", _boom)

    with app.app_context():
        report = scan_url("https://example.com")

    redirect_result = next(r for r in report.rule_results if r.rule == "redirect_check")
    assert redirect_result.detail == "simulated rule bug"
    assert redirect_result.impact == 0
    # the rest of the scan still completed normally
    assert report.trust_score >= 90


def test_external_threat_intel_match_drives_score_to_zero_and_dangerous(app, monkeypatch):
    """End-to-end (through the full scan_url() engine, not just the rule in
    isolation): a confirmed external threat-intel match still produces the
    documented -100 impact, clamps the score to 0, and classifies as
    Dangerous -- exactly as before this priority's provider-reliability
    changes. Mocked; never touches a live provider or a real URL."""
    monkeypatch.setattr(
        external_threat_intel,
        "evaluate",
        lambda ctx: RuleResult(
            rule="external_threat_intel",
            label="Global Threat Intelligence",
            triggered=True,
            impact=-100,
            severity="critical",
            message="Verified threat on URLhaus feed (malware, status: online).",
            detail="Verified threat on URLhaus feed (malware, status: online).",
        ),
    )
    with app.app_context():
        report = scan_url("https://example.com")
    assert report.trust_score == 0
    assert report.risk_level == RiskLevel.DANGEROUS
    ti_result = next(r for r in report.rule_results if r.rule == "external_threat_intel")
    assert ti_result.triggered
    assert ti_result.impact == -100


def test_quick_classify_is_network_free_and_fast(app):
    """Used for triaging links found in emails — must never touch the
    network, since an email can contain many links."""
    with app.app_context():
        start = time.monotonic()
        score, risk = quick_classify("http://192.168.10.2/login-verify-account")
        elapsed = time.monotonic() - start

    assert elapsed < 1
    assert risk == RiskLevel.DANGEROUS
    assert 0 <= score <= 100


def test_quick_classify_flags_typosquat(app):
    with app.app_context():
        score, risk = quick_classify("https://paypaI.com/signin")
    assert risk in {RiskLevel.SUSPICIOUS, RiskLevel.DANGEROUS}


def test_quick_classify_clean_url_scores_high(app):
    with app.app_context():
        score, risk = quick_classify("https://example.com/about")
    assert risk == RiskLevel.SAFE
    assert score >= 90


def test_quick_classify_and_scan_url_intentionally_run_different_rule_sets():
    """quick_classify and scan_url are NOT required to agree on the same
    URL's score — quick_classify skips the 4 network-bound rules entirely,
    so a URL whose score depends on one of them (e.g. an SSL/domain-age/
    redirect/threat-intel finding) can legitimately score differently
    through each path. This pins that architectural split so it can't
    silently erode (e.g. by someone "fixing" a rule into the wrong set)."""
    cpu_only_names = {engine._rule_name(r) for r in engine.CPU_ONLY_RULES}
    assert cpu_only_names.isdisjoint(engine.NETWORK_BOUND_RULE_NAMES)
    assert engine.NETWORK_BOUND_RULE_NAMES == {
        "ssl_certificate",
        "domain_age",
        "redirect_check",
        "external_threat_intel",
    }


def test_quick_classify_vs_scan_url_can_legitimately_diverge(app, monkeypatch):
    """End-to-end demonstration (not just the rule-set split above): forcing
    a network-bound rule to fire changes scan_url's score but not
    quick_classify's, for the identical URL."""
    monkeypatch.setattr(
        ssl_certificate,
        "evaluate",
        lambda ctx: RuleResult(
            rule="ssl_certificate",
            label="SSL Certificate",
            triggered=True,
            impact=-20,
            severity="high",
            message="forced for test",
        ),
    )

    with app.app_context():
        full_report = scan_url("https://example.com/about")
        quick_score, _ = quick_classify("https://example.com/about")

    assert full_report.trust_score == 80  # 100 - 20 from the forced ssl finding
    assert quick_score == 100  # quick_classify never ran ssl_certificate at all
    assert full_report.trust_score != quick_score
