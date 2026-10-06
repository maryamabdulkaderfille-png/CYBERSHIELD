from tests.conftest import csrf_header

_EXPECTED_KEYS = {
    "overall_security_score",
    "threat_trend",
    "recent_threat_timeline",
    "weekly_activity",
    "monthly_activity",
    "scan_distribution",
    "risk_distribution",
    "most_dangerous_domains",
    "most_common_keywords",
    "most_common_scanner",
    "threat_heatmap",
    "average_scan_duration_ms",
    "detection_accuracy",
    "recent_notifications",
    "unread_notification_count",
}


def _login(client, registered_user):
    client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )


def test_dashboard_requires_auth(client):
    assert client.get("/api/v1/dashboard").status_code == 401


def test_dashboard_empty_state(client, registered_user):
    _login(client, registered_user)
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    body = response.get_json()
    assert _EXPECTED_KEYS.issubset(body.keys())
    assert body["overall_security_score"] is None
    assert body["most_common_scanner"] is None
    assert body["average_scan_duration_ms"] is None
    assert len(body["weekly_activity"]) == 7
    assert len(body["monthly_activity"]) == 30
    assert len(body["threat_heatmap"]) == 7
    assert body["detection_accuracy"]["available"] is False


def test_dashboard_reflects_scan_activity(client, registered_user):
    _login(client, registered_user)
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))
    client.post(
        "/api/v1/url/scan",
        json={"url": "http://8.8.8.8/login-verify-secure-bank-wallet"},
        headers=csrf_header(client),
    )

    response = client.get("/api/v1/dashboard")
    body = response.get_json()
    assert body["scan_distribution"]["url"] == 2
    assert body["most_common_scanner"] == "url"
    assert body["overall_security_score"] is not None
    assert body["average_scan_duration_ms"] is not None
    assert body["average_scan_duration_ms"] >= 0
    assert sum(body["risk_distribution"].values()) == 2
    assert body["unread_notification_count"] == 1  # the dangerous scan
    assert len(body["recent_notifications"]) == 1


def test_dashboard_most_dangerous_domains(client, registered_user):
    _login(client, registered_user)
    client.post(
        "/api/v1/url/scan",
        json={"url": "http://8.8.8.8/login-verify-secure-bank-wallet"},
        headers=csrf_header(client),
    )

    response = client.get("/api/v1/dashboard")
    domains = response.get_json()["most_dangerous_domains"]
    assert len(domains) == 1
    assert domains[0]["domain"] == "8.8.8.8"
    assert domains[0]["count"] == 1


def test_dashboard_scoped_to_own_user(client, registered_user):
    _login(client, registered_user)
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))
    client.post("/api/v1/auth/logout", headers=csrf_header(client))

    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Other User",
            "username": "otheruser_dash",
            "email": "other_dash@example.com",
            "password": "StrongPass1!",
            "confirm_password": "StrongPass1!",
        },
    )
    response = client.get("/api/v1/dashboard")
    assert response.get_json()["scan_distribution"]["url"] == 0
