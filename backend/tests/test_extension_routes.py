from tests.conftest import csrf_header


def _login(client, registered_user):
    client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )


def test_ephemeral_scan_requires_auth(client):
    response = client.post("/api/v1/extension/scan", json={"url": "https://example.com"})
    assert response.status_code == 401


def test_ephemeral_scan_rejects_malformed_url(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/extension/scan", json={"url": "not-a-url"}, headers=csrf_header(client)
    )
    assert response.status_code == 422


def test_ephemeral_scan_returns_report_without_persisting(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/extension/scan", json={"url": "https://example.com"}, headers=csrf_header(client)
    )
    assert response.status_code == 200
    body = response.get_json()
    assert 0 <= body["trust_score"] <= 100
    assert body["risk"] in {"Safe", "Low Risk", "Suspicious", "Dangerous"}
    assert isinstance(body["reasons"], list)
    assert isinstance(body["recommendations"], list)
    assert isinstance(body["rules"], list)
    assert len(body["rules"]) == 13
    assert body["persisted"] is False

    # Nothing was written to the user's real scan history.
    history = client.get("/api/v1/url/history").get_json()
    assert history["total"] == 0

    # Nor to the unified Scan Center.
    unified = client.get("/api/v1/scans").get_json()
    assert unified["total"] == 0


def test_ephemeral_scan_does_not_create_notification(client, registered_user):
    _login(client, registered_user)
    client.post(
        "/api/v1/extension/scan",
        json={"url": "http://8.8.8.8/login-verify-secure-bank-wallet"},
        headers=csrf_header(client),
    )
    notifications = client.get("/api/v1/notifications").get_json()
    assert notifications["total"] == 0


def test_ephemeral_scan_detects_dangerous_url(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/extension/scan",
        json={"url": "http://8.8.8.8/login-verify-secure-bank-wallet"},
        headers=csrf_header(client),
    )
    assert response.get_json()["risk"] == "Dangerous"


def test_ephemeral_scan_rejects_missing_url(client, registered_user):
    _login(client, registered_user)
    response = client.post("/api/v1/extension/scan", json={}, headers=csrf_header(client))
    assert response.status_code == 422
