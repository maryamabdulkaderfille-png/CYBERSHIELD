from tests.conftest import csrf_header
from app.extensions import db as _db
from app.models.blacklist import BlacklistEntry

_EXPECTED_KEYS = {
    "known_phishing_domains",
    "suspicious_domains",
    "recently_blocked_domains",
    "top_targeted_brands",
    "most_common_keywords",
    "attack_categories",
    "threat_statistics",
    "severity_distribution",
    "detection_trends",
    "blacklist_overview",
    "threat_feed_architecture",
}


def _login(client, registered_user):
    client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )


def test_summary_requires_auth(client):
    assert client.get("/api/v1/threats").status_code == 401


def test_summary_shape(client, registered_user):
    _login(client, registered_user)
    response = client.get("/api/v1/threats")
    assert response.status_code == 200
    body = response.get_json()
    assert _EXPECTED_KEYS.issubset(body.keys())
    assert body["threat_feed_architecture"]["live_feed_enabled"] is False


def test_summary_reflects_dangerous_scan(client, registered_user):
    _login(client, registered_user)
    client.post(
        "/api/v1/url/scan",
        json={"url": "http://8.8.8.8/login-verify-secure-bank-wallet"},
        headers=csrf_header(client),
    )

    response = client.get("/api/v1/threats")
    body = response.get_json()
    assert body["threat_statistics"]["total_scans"] == 1
    assert body["threat_statistics"]["dangerous_count"] == 1
    assert body["severity_distribution"]["dangerous"] == 1


def test_blacklisted_domain_appears_in_known_phishing_domains(client, app, registered_user):
    with app.app_context():
        _db.session.add(BlacklistEntry(domain="evil-phish.example", reason="Reported phishing site"))
        _db.session.commit()

    _login(client, registered_user)
    response = client.get("/api/v1/threats")
    domains = {d["domain"] for d in response.get_json()["known_phishing_domains"]}
    assert "evil-phish.example" in domains
    assert response.get_json()["blacklist_overview"]["total"] == 1


def test_domains_endpoint_requires_auth(client):
    assert client.get("/api/v1/threats/domains").status_code == 401


def test_domains_endpoint_lists_scanned_domains(client, registered_user):
    _login(client, registered_user)
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))

    response = client.get("/api/v1/threats/domains")
    assert response.status_code == 200
    body = response.get_json()
    domains = {item["domain"] for item in body["items"]}
    assert "example.com" in domains


def test_domains_endpoint_search_filter(client, registered_user):
    _login(client, registered_user)
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))
    client.post(
        "/api/v1/url/scan",
        json={"url": "http://8.8.8.8/login-verify-secure-bank-wallet"},
        headers=csrf_header(client),
    )

    response = client.get("/api/v1/threats/domains?search=example")
    body = response.get_json()
    assert all("example" in item["domain"] for item in body["items"])


def test_domains_endpoint_risk_level_filter(client, registered_user):
    _login(client, registered_user)
    client.post(
        "/api/v1/url/scan",
        json={"url": "http://8.8.8.8/login-verify-secure-bank-wallet"},
        headers=csrf_header(client),
    )
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))

    response = client.get("/api/v1/threats/domains?risk_level=Dangerous")
    body = response.get_json()
    assert all(item["risk_level"] == "Dangerous" for item in body["items"])
    assert len(body["items"]) == 1


def test_domains_endpoint_pagination(client, registered_user):
    _login(client, registered_user)
    for i in range(3):
        client.post(
            "/api/v1/url/scan", json={"url": f"https://example{i}.com"}, headers=csrf_header(client)
        )

    response = client.get("/api/v1/threats/domains?page=1&per_page=2")
    body = response.get_json()
    assert len(body["items"]) == 2
    assert body["total"] == 3
    assert body["total_pages"] == 2


def test_domains_endpoint_rejects_invalid_sort(client, registered_user):
    _login(client, registered_user)
    response = client.get("/api/v1/threats/domains?sort_by=invalid")
    assert response.status_code == 422


def test_export_placeholder_returns_501(client, registered_user):
    _login(client, registered_user)
    response = client.get("/api/v1/threats/export")
    assert response.status_code == 501
