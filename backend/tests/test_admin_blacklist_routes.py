from tests.conftest import csrf_header


def _login(client, user):
    client.post("/api/v1/auth/login", json={"email": user["email"], "password": user["password"]})


def test_list_requires_admin(client, registered_user):
    _login(client, registered_user)
    assert client.get("/api/v1/admin/blacklist").status_code == 403


def test_add_and_list_entry(client, admin_user):
    _login(client, admin_user)
    response = client.post(
        "/api/v1/admin/blacklist",
        json={"domain": "evil-phish.example", "reason": "Reported by a user"},
        headers=csrf_header(client),
    )
    assert response.status_code == 201
    entry = response.get_json()["entry"]
    assert entry["domain"] == "evil-phish.example"
    assert entry["enabled"] is True
    assert entry["added_by_user_id"] is not None

    listed = client.get("/api/v1/admin/blacklist").get_json()
    assert listed["total"] == 1


def test_add_rejects_duplicate_domain(client, admin_user):
    _login(client, admin_user)
    client.post(
        "/api/v1/admin/blacklist", json={"domain": "evil-phish.example"}, headers=csrf_header(client)
    )
    response = client.post(
        "/api/v1/admin/blacklist", json={"domain": "evil-phish.example"}, headers=csrf_header(client)
    )
    assert response.status_code == 409


def test_add_normalizes_www_prefix_to_registrable_domain(client, admin_user):
    _login(client, admin_user)
    client.post(
        "/api/v1/admin/blacklist", json={"domain": "www.evil-phish.example"}, headers=csrf_header(client)
    )
    response = client.post(
        "/api/v1/admin/blacklist", json={"domain": "evil-phish.example"}, headers=csrf_header(client)
    )
    assert response.status_code == 409  # same registrable domain, already present


def test_add_rejects_full_url_instead_of_bare_domain(client, admin_user):
    _login(client, admin_user)
    response = client.post(
        "/api/v1/admin/blacklist", json={"domain": "https://evil.example/phish"}, headers=csrf_header(client)
    )
    assert response.status_code == 422


def test_disable_then_enable_entry(client, admin_user):
    _login(client, admin_user)
    entry = client.post(
        "/api/v1/admin/blacklist", json={"domain": "evil-phish.example"}, headers=csrf_header(client)
    ).get_json()["entry"]

    disabled = client.put(f"/api/v1/admin/blacklist/{entry['id']}/disable", headers=csrf_header(client))
    assert disabled.get_json()["entry"]["enabled"] is False

    enabled = client.put(f"/api/v1/admin/blacklist/{entry['id']}/enable", headers=csrf_header(client))
    assert enabled.get_json()["entry"]["enabled"] is True


def test_disabling_blacklist_entry_stops_it_from_flagging_scans(client, admin_user):
    _login(client, admin_user)
    entry = client.post(
        "/api/v1/admin/blacklist", json={"domain": "disable-me-phish.example"}, headers=csrf_header(client)
    ).get_json()["entry"]

    scan = client.post(
        "/api/v1/url/scan", json={"url": "https://disable-me-phish.example/login"}, headers=csrf_header(client)
    ).get_json()
    assert scan["risk"] == "Dangerous"

    client.put(f"/api/v1/admin/blacklist/{entry['id']}/disable", headers=csrf_header(client))

    scan2 = client.post(
        "/api/v1/url/scan", json={"url": "https://disable-me-phish.example/login2"}, headers=csrf_header(client)
    ).get_json()
    assert not any(r["rule"] == "blacklist_check" and r["triggered"] for r in scan2["rules"])


def test_remove_entry(client, admin_user):
    _login(client, admin_user)
    entry = client.post(
        "/api/v1/admin/blacklist", json={"domain": "evil-phish.example"}, headers=csrf_header(client)
    ).get_json()["entry"]

    response = client.delete(f"/api/v1/admin/blacklist/{entry['id']}", headers=csrf_header(client))
    assert response.status_code == 200
    assert client.get("/api/v1/admin/blacklist").get_json()["total"] == 0


def test_blacklist_changes_are_audited(client, admin_user):
    _login(client, admin_user)
    client.post(
        "/api/v1/admin/blacklist", json={"domain": "evil-phish.example"}, headers=csrf_header(client)
    )
    logs = client.get("/api/v1/admin/audit-logs?action=blacklist_update").get_json()["items"]
    assert len(logs) == 1
    assert logs[0]["details"]["domain"] == "evil-phish.example"
