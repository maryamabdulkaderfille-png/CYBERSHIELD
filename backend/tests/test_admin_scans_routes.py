from tests.conftest import csrf_header


def _login(client, user):
    client.post("/api/v1/auth/login", json={"email": user["email"], "password": user["password"]})


def test_list_all_scans_requires_admin(client, registered_user):
    _login(client, registered_user)
    assert client.get("/api/v1/admin/scans").status_code == 403


def test_list_all_scans_spans_every_user(client, admin_user, registered_user):
    _login(client, registered_user)
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))
    client.post("/api/v1/auth/logout", headers=csrf_header(client))

    _login(client, admin_user)
    client.post("/api/v1/url/scan", json={"url": "https://another-example.com"}, headers=csrf_header(client))

    response = client.get("/api/v1/admin/scans")
    assert response.status_code == 200
    body = response.get_json()
    assert body["total"] == 2
    usernames = {item["username"] for item in body["items"]}
    assert "janedoe" in usernames
    assert "adaadmin" in usernames


def test_list_scans_filters_by_source(client, admin_user):
    _login(client, admin_user)
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))
    client.post(
        "/api/v1/url/scan",
        json={"url": "https://from-extension.example.com"},
        headers={**csrf_header(client), "X-CyberShield-Client": "extension"},
    )

    web_only = client.get("/api/v1/admin/scans?source=web").get_json()
    ext_only = client.get("/api/v1/admin/scans?source=extension").get_json()
    assert web_only["total"] == 1
    assert ext_only["total"] == 1
    assert ext_only["items"][0]["source"] == "extension"


def test_admin_can_delete_any_users_scan(client, admin_user, registered_user):
    _login(client, registered_user)
    created = client.post(
        "/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client)
    ).get_json()
    client.post("/api/v1/auth/logout", headers=csrf_header(client))

    _login(client, admin_user)
    response = client.delete(f"/api/v1/admin/scans/url/{created['id']}", headers=csrf_header(client))
    assert response.status_code == 200

    assert client.get("/api/v1/admin/scans").get_json()["total"] == 0


def test_admin_bulk_delete_across_users(client, admin_user, registered_user):
    _login(client, registered_user)
    created = client.post(
        "/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client)
    ).get_json()
    client.post("/api/v1/auth/logout", headers=csrf_header(client))

    _login(client, admin_user)
    own = client.post(
        "/api/v1/url/scan", json={"url": "https://another.example.com"}, headers=csrf_header(client)
    ).get_json()

    response = client.post(
        "/api/v1/admin/scans/bulk-delete",
        json={"items": [{"scanner_type": "url", "id": created["id"]}, {"scanner_type": "url", "id": own["id"]}]},
        headers=csrf_header(client),
    )
    assert response.status_code == 200
    assert response.get_json()["deleted_count"] == 2


def test_scan_deletion_is_audited(client, admin_user, registered_user):
    _login(client, registered_user)
    created = client.post(
        "/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client)
    ).get_json()
    client.post("/api/v1/auth/logout", headers=csrf_header(client))

    _login(client, admin_user)
    client.delete(f"/api/v1/admin/scans/url/{created['id']}", headers=csrf_header(client))

    logs = client.get("/api/v1/admin/audit-logs?action=scan_deleted").get_json()["items"]
    assert any(log["details"].get("admin_action") for log in logs)


def test_export_placeholder_returns_501(client, admin_user):
    _login(client, admin_user)
    assert client.get("/api/v1/admin/scans/export").status_code == 501
