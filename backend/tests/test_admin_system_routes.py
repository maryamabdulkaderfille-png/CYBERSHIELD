def _login(client, user):
    client.post("/api/v1/auth/login", json={"email": user["email"], "password": user["password"]})


def test_system_health_requires_admin(client, registered_user):
    _login(client, registered_user)
    assert client.get("/api/v1/admin/system/health").status_code == 403


def test_system_health_shape(client, admin_user):
    _login(client, admin_user)
    response = client.get("/api/v1/admin/system/health")
    assert response.status_code == 200
    body = response.get_json()
    assert body["database"]["status"] == "healthy"
    assert body["memory"]["available"] is False  # honest placeholder, not fabricated
    assert "request_metrics" in body
    assert body["uptime_seconds"] >= 0


def test_system_health_reports_threat_intel_configuration_without_exposing_keys(client, admin_user, monkeypatch):
    monkeypatch.delenv("URLHAUS_AUTH_KEY", raising=False)
    monkeypatch.delenv("VIRUSTOTAL_API_KEY", raising=False)
    _login(client, admin_user)
    response = client.get("/api/v1/admin/system/health")
    body = response.get_json()
    assert body["threat_intelligence"]["urlhaus"] == {"configured": False}
    assert body["threat_intelligence"]["virustotal"] == {"configured": False}
    assert "URLHAUS_AUTH_KEY" not in str(body)
    assert "VIRUSTOTAL_API_KEY" not in str(body)


def test_request_metrics_reflect_real_traffic(client, admin_user):
    _login(client, admin_user)
    client.get("/api/v1/admin/system/health")
    client.get("/api/v1/admin/system/health")

    response = client.get("/api/v1/admin/system/health")
    metrics = response.get_json()["request_metrics"]
    assert metrics["total_requests"] >= 3
    assert metrics["average_response_time_ms"] is not None
    assert metrics["error_rate_percent"] is not None
