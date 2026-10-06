from tests.conftest import csrf_header


def _login(client, user):
    client.post("/api/v1/auth/login", json={"email": user["email"], "password": user["password"]})


def test_list_requires_admin(client, registered_user):
    _login(client, registered_user)
    assert client.get("/api/v1/admin/audit-logs").status_code == 403


def test_login_and_logout_are_audited(client, admin_user):
    _login(client, admin_user)
    client.post("/api/v1/auth/logout", headers=csrf_header(client))
    _login(client, admin_user)

    response = client.get("/api/v1/admin/audit-logs")
    assert response.status_code == 200
    actions = [log["action"] for log in response.get_json()["items"]]
    assert "login" in actions
    assert "logout" in actions


def test_failed_login_is_audited_with_failure_status(client, admin_user, registered_user):
    client.post("/api/v1/auth/login", json={"email": registered_user["email"], "password": "WrongPassword1!"})

    _login(client, admin_user)
    logs = client.get("/api/v1/admin/audit-logs?action=login&status=failure").get_json()["items"]
    assert len(logs) == 1
    assert logs[0]["status"] == "failure"
    assert logs[0]["details"]["email"] == registered_user["email"]
    assert logs[0]["user_id"] is None


def test_profile_and_settings_updates_are_audited(client, admin_user):
    _login(client, admin_user)
    client.put("/api/v1/profile", json={"bio": "hello"}, headers=csrf_header(client))
    client.put("/api/v1/settings", json={"theme": "dark"}, headers=csrf_header(client))

    logs = client.get("/api/v1/admin/audit-logs").get_json()["items"]
    actions = [log["action"] for log in logs]
    assert "profile_update" in actions
    assert "settings_update" in actions


def test_report_generation_is_audited(client, admin_user):
    _login(client, admin_user)
    scan = client.post(
        "/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client)
    ).get_json()
    client.get(f"/api/v1/reports/url/{scan['id']}")

    logs = client.get("/api/v1/admin/audit-logs?action=report_generated").get_json()["items"]
    assert len(logs) == 1


def test_extension_scan_is_audited_as_extension_event(client, admin_user):
    _login(client, admin_user)
    client.post(
        "/api/v1/url/scan",
        json={"url": "https://example.com"},
        headers={**csrf_header(client), "X-CyberShield-Client": "extension"},
    )
    logs = client.get("/api/v1/admin/audit-logs?action=extension_event").get_json()["items"]
    assert len(logs) == 1


def test_privacy_mode_ephemeral_scan_is_never_audited(client, admin_user):
    _login(client, admin_user)
    client.post(
        "/api/v1/extension/scan",
        json={"url": "https://example.com"},
        headers={**csrf_header(client), "X-CyberShield-Client": "extension"},
    )
    logs = client.get("/api/v1/admin/audit-logs").get_json()["items"]
    assert not any(log["action"] == "extension_event" for log in logs)


def test_filter_by_action(client, admin_user):
    _login(client, admin_user)
    client.put("/api/v1/profile", json={"bio": "hello"}, headers=csrf_header(client))

    response = client.get("/api/v1/admin/audit-logs?action=profile_update")
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["action"] == "profile_update"


def test_pagination(client, admin_user):
    _login(client, admin_user)
    for i in range(3):
        client.put("/api/v1/profile", json={"bio": f"hello {i}"}, headers=csrf_header(client))

    response = client.get("/api/v1/admin/audit-logs?action=profile_update&page=1&per_page=2")
    body = response.get_json()
    assert len(body["items"]) == 2
    assert body["total"] == 3


def test_filter_by_date_range_excludes_entries_outside_it(client, admin_user):
    _login(client, admin_user)
    client.put("/api/v1/profile", json={"bio": "hello"}, headers=csrf_header(client))

    future_start = "2999-01-01T00:00:00Z"
    response = client.get(f"/api/v1/admin/audit-logs?action=profile_update&date_from={future_start}")
    assert response.get_json()["total"] == 0

    past_start = "2000-01-01T00:00:00Z"
    response = client.get(f"/api/v1/admin/audit-logs?action=profile_update&date_from={past_start}")
    assert response.get_json()["total"] == 1


def test_date_from_after_date_to_is_rejected(client, admin_user):
    _login(client, admin_user)
    response = client.get(
        "/api/v1/admin/audit-logs?date_from=2026-01-02T00:00:00Z&date_to=2026-01-01T00:00:00Z"
    )
    assert response.status_code == 422
