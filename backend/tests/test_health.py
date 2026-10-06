def test_health_endpoint_reports_ok_with_database_status(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "cybershield-backend"
    assert data["database"]["status"] == "healthy"


def test_health_endpoint_is_unauthenticated(client):
    # A Docker/orchestrator healthcheck has no session — this must never 401.
    response = client.get("/health")
    assert response.status_code != 401
