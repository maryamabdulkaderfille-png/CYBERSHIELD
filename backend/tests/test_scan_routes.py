from tests.conftest import csrf_header


def _login(client, registered_user):
    client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )


def test_scan_requires_auth(client):
    response = client.post("/api/v1/url/scan", json={"url": "https://example.com"})
    assert response.status_code == 401


def test_scan_rejects_malformed_url(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/url/scan", json={"url": "not-a-url"}, headers=csrf_header(client)
    )
    assert response.status_code == 422


def test_scan_rejects_missing_url(client, registered_user):
    _login(client, registered_user)
    response = client.post("/api/v1/url/scan", json={}, headers=csrf_header(client))
    assert response.status_code == 422


def test_scan_rejects_excessively_long_url(client, registered_user):
    _login(client, registered_user)
    huge_url = "https://example.com/" + "a" * 3000
    response = client.post(
        "/api/v1/url/scan", json={"url": huge_url}, headers=csrf_header(client)
    )
    assert response.status_code == 422


def test_scan_rejects_non_http_scheme(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/url/scan", json={"url": "ftp://example.com"}, headers=csrf_header(client)
    )
    assert response.status_code == 422


def test_scan_valid_url_returns_report(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client)
    )
    assert response.status_code == 201
    body = response.get_json()
    assert "trust_score" in body
    assert 0 <= body["trust_score"] <= 100
    assert body["risk"] in {"Safe", "Low Risk", "Suspicious", "Dangerous"}
    assert isinstance(body["reasons"], list)
    assert isinstance(body["recommendations"], list)
    assert isinstance(body["rules"], list)
    assert len(body["rules"]) == 13


def test_scan_is_persisted_and_appears_in_history(client, registered_user):
    _login(client, registered_user)
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))

    response = client.get("/api/v1/url/history")
    assert response.status_code == 200
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["url"] == "https://example.com"


def test_history_requires_auth(client):
    response = client.get("/api/v1/url/history")
    assert response.status_code == 401


def test_history_search_filters_by_url(client, registered_user):
    _login(client, registered_user)
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))
    client.post("/api/v1/url/scan", json={"url": "https://paypaI.com/login"}, headers=csrf_header(client))

    response = client.get("/api/v1/url/history?search=paypa")
    body = response.get_json()
    assert body["total"] == 1
    assert "paypaI" in body["items"][0]["url"]


def test_history_filters_by_risk_level(client, registered_user):
    _login(client, registered_user)
    client.post(
        "/api/v1/url/scan",
        json={"url": "http://8.8.8.8/login-verify-secure-bank-wallet"},
        headers=csrf_header(client),
    )
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))

    response = client.get("/api/v1/url/history?risk_level=Dangerous")
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["risk_level"] == "Dangerous"


def test_history_pagination(client, registered_user):
    _login(client, registered_user)
    for i in range(5):
        client.post(
            "/api/v1/url/scan", json={"url": f"https://example.com/page-{i}"}, headers=csrf_header(client)
        )

    response = client.get("/api/v1/url/history?page=1&per_page=2")
    body = response.get_json()
    assert len(body["items"]) == 2
    assert body["total"] == 5
    assert body["total_pages"] == 3


def test_scan_detail_endpoint(client, registered_user):
    _login(client, registered_user)
    created = client.post(
        "/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client)
    ).get_json()

    response = client.get(f"/api/v1/url/history/{created['id']}")
    assert response.status_code == 200
    assert response.get_json()["url"] == "https://example.com"


def test_scan_detail_not_found_for_other_users_scan(client, registered_user):
    _login(client, registered_user)
    created = client.post(
        "/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client)
    ).get_json()
    client.post("/api/v1/auth/logout", headers=csrf_header(client))

    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Other User",
            "username": "otheruser",
            "email": "other@example.com",
            "password": "StrongPass1!",
            "confirm_password": "StrongPass1!",
        },
    )
    response = client.get(f"/api/v1/url/history/{created['id']}")
    assert response.status_code == 404


def test_stats_endpoint_aggregates_scans(client, registered_user):
    _login(client, registered_user)
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))
    client.post(
        "/api/v1/url/scan",
        json={"url": "http://8.8.8.8/login-verify-secure-bank-wallet"},
        headers=csrf_header(client),
    )

    response = client.get("/api/v1/url/stats")
    assert response.status_code == 200
    body = response.get_json()
    assert body["total_scans"] == 2
    assert body["safe_count"] + body["low_risk_count"] + body["suspicious_count"] + body["dangerous_count"] == 2
    assert len(body["recent_scans"]) == 2
    assert body["average_trust_score"] is not None


def test_blacklisted_domain_is_flagged_in_scan(app, client, registered_user):
    from app.extensions import db
    from app.models.blacklist import BlacklistEntry

    with app.app_context():
        db.session.add(BlacklistEntry(domain="known-phish.example", reason="Reported phishing site"))
        db.session.commit()

    _login(client, registered_user)
    response = client.post(
        "/api/v1/url/scan", json={"url": "https://known-phish.example/login"}, headers=csrf_header(client)
    )
    body = response.get_json()
    assert body["risk"] == "Dangerous"
    assert any("blacklist" in reason.lower() for reason in body["reasons"])


def test_external_threat_intel_match_propagates_through_real_scan_route(client, registered_user, monkeypatch):
    """Proves the MATCH/CLEAN/UNAVAILABLE fix isn't just correct in rule-level
    unit tests -- it propagates all the way through the real production
    route: POST /api/v1/url/scan -> scan_service -> scan_url() -> rules ->
    response JSON. Mocks the provider boundary only; no live provider call,
    no real/malicious URL."""
    from app.services.url_scanner.rules import external_threat_intel
    from app.services.url_scanner.types import RuleResult

    monkeypatch.setattr(
        external_threat_intel,
        "evaluate",
        lambda ctx: RuleResult(
            rule="external_threat_intel",
            label="Global Threat Intelligence",
            triggered=True,
            impact=-100,
            severity="critical",
            message="Flagged as malicious by 12 security vendors on VirusTotal.",
            detail="Flagged as malicious by 12 security vendors on VirusTotal.",
        ),
    )
    _login(client, registered_user)
    response = client.post(
        "/api/v1/url/scan", json={"url": "https://unrelated-test-domain.example"}, headers=csrf_header(client)
    )
    body = response.get_json()
    assert response.status_code == 201
    assert body["trust_score"] == 0
    assert body["risk"] == "Dangerous"
    ti_entry = next(r for r in body["rules"] if r["rule"] == "external_threat_intel")
    assert ti_entry["triggered"] is True
    assert ti_entry["impact"] == -100
    assert "VirusTotal" in ti_entry["message"]


def test_external_threat_intel_unavailable_propagates_through_real_scan_route(client, registered_user, monkeypatch):
    """The UNAVAILABLE case must also be visible end-to-end in the real API
    response, not silently collapse into the generic "clean" message."""
    from app.services.url_scanner.rules import external_threat_intel
    from app.services.url_scanner.types import RuleResult

    monkeypatch.setattr(
        external_threat_intel,
        "evaluate",
        lambda ctx: RuleResult(
            rule="external_threat_intel",
            label="Global Threat Intelligence",
            triggered=False,
            impact=0,
            severity="info",
            message="Global threat-intelligence check could not be completed — result unknown, not confirmed clean.",
            detail="unavailable:virustotal=missing_auth_key,urlhaus=missing_auth_key",
        ),
    )
    _login(client, registered_user)
    response = client.post(
        "/api/v1/url/scan", json={"url": "https://unrelated-test-domain-2.example"}, headers=csrf_header(client)
    )
    body = response.get_json()
    assert response.status_code == 201
    ti_entry = next(r for r in body["rules"] if r["rule"] == "external_threat_intel")
    assert ti_entry["triggered"] is False
    assert ti_entry["impact"] == 0
    assert ti_entry["message"] != "Target is clean and not listed on global threat intelligence feeds."
    assert ti_entry["detail"].startswith("unavailable:")
