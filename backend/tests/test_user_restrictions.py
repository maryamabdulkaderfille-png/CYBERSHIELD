from tests.conftest import csrf_header


def _login(client, user):
    client.post("/api/v1/auth/login", json={"email": user["email"], "password": user["password"]})


def _target_id(client, search="jane"):
    users = client.get(f"/api/v1/admin/users?search={search}").get_json()["items"]
    return users[0]["id"]


def _restrict(client, target_id, feature):
    return client.post(
        f"/api/v1/admin/users/{target_id}/restrictions", json={"feature": feature}, headers=csrf_header(client)
    )


def _unrestrict(client, target_id, feature):
    return client.delete(f"/api/v1/admin/users/{target_id}/restrictions/{feature}", headers=csrf_header(client))


# --- Admin CRUD --------------------------------------------------------------


def test_add_restriction_requires_admin(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        f"/api/v1/admin/users/{registered_user['email']}/restrictions",
        json={"feature": "url"},
        headers=csrf_header(client),
    )
    assert response.status_code == 403


def test_add_and_list_restriction(client, admin_user, registered_user):
    _login(client, admin_user)
    target_id = _target_id(client)

    response = _restrict(client, target_id, "url")
    assert response.status_code == 201
    assert response.get_json()["restriction"]["feature"] == "url"

    items = client.get(f"/api/v1/admin/users/{target_id}/restrictions").get_json()["items"]
    assert any(r["feature"] == "url" for r in items)


def test_adding_the_same_restriction_twice_is_idempotent(client, admin_user, registered_user):
    _login(client, admin_user)
    target_id = _target_id(client)

    _restrict(client, target_id, "url")
    _restrict(client, target_id, "url")

    items = client.get(f"/api/v1/admin/users/{target_id}/restrictions").get_json()["items"]
    assert len([r for r in items if r["feature"] == "url"]) == 1


def test_remove_restriction_lifts_it(client, admin_user, registered_user):
    _login(client, admin_user)
    target_id = _target_id(client)
    _restrict(client, target_id, "url")

    response = _unrestrict(client, target_id, "url")
    assert response.status_code == 200

    items = client.get(f"/api/v1/admin/users/{target_id}/restrictions").get_json()["items"]
    assert not any(r["feature"] == "url" for r in items)


def test_remove_nonexistent_restriction_404s(client, admin_user, registered_user):
    _login(client, admin_user)
    target_id = _target_id(client)
    response = _unrestrict(client, target_id, "qr")
    assert response.status_code == 404


def test_invalid_feature_rejected(client, admin_user, registered_user):
    _login(client, admin_user)
    target_id = _target_id(client)
    response = _restrict(client, target_id, "not_a_real_feature")
    assert response.status_code == 422


def test_restriction_changes_are_audited(client, admin_user, registered_user):
    _login(client, admin_user)
    target_id = _target_id(client)
    _restrict(client, target_id, "email")
    _unrestrict(client, target_id, "email")

    logs = client.get("/api/v1/admin/audit-logs?action=admin_action").get_json()["items"]
    details = [log["details"] for log in logs]
    assert any(d.get("action_detail") == "restriction_added" and d.get("feature") == "email" for d in details)
    assert any(d.get("action_detail") == "restriction_removed" and d.get("feature") == "email" for d in details)


# --- Server-side enforcement --------------------------------------------------


def test_url_restriction_blocks_url_scan(client, admin_user, registered_user):
    _login(client, admin_user)
    target_id = _target_id(client)
    _restrict(client, target_id, "url")

    _login(client, registered_user)
    response = client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))
    assert response.status_code == 403


def test_url_restriction_blocks_extension_scan_too(client, admin_user, registered_user):
    """Confirms the deliberate scope decision: a 'url' restriction also
    gates the browser extension's ephemeral scan endpoint, since it's the
    same underlying capability."""
    _login(client, admin_user)
    target_id = _target_id(client)
    _restrict(client, target_id, "url")

    _login(client, registered_user)
    response = client.post(
        "/api/v1/extension/scan", json={"url": "https://example.com"}, headers=csrf_header(client)
    )
    assert response.status_code == 403


def test_lifting_url_restriction_restores_access(client, admin_user, registered_user):
    _login(client, admin_user)
    target_id = _target_id(client)
    _restrict(client, target_id, "url")
    _unrestrict(client, target_id, "url")

    _login(client, registered_user)
    response = client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))
    assert response.status_code == 201


def test_email_restriction_blocks_email_scan(client, admin_user, registered_user):
    _login(client, admin_user)
    target_id = _target_id(client)
    _restrict(client, target_id, "email")

    _login(client, registered_user)
    response = client.post(
        "/api/v1/email/scan", data={"email_text": "From: a@b.com\nTo: c@d.com\nSubject: hi\n\nbody"},
        headers=csrf_header(client),
    )
    assert response.status_code == 403


def test_qr_restriction_blocks_qr_scan(client, admin_user, registered_user):
    _login(client, admin_user)
    target_id = _target_id(client)
    _restrict(client, target_id, "qr")

    _login(client, registered_user)
    response = client.post("/api/v1/qr/scan", data={}, headers=csrf_header(client))
    # 403 (restricted) must win over 422 (missing file) — the restriction
    # check runs before any request-body validation.
    assert response.status_code == 403


def test_reports_restriction_blocks_report_view_regardless_of_scanner_type(client, admin_user, registered_user):
    _login(client, registered_user)
    scan = client.post(
        "/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client)
    ).get_json()

    _login(client, admin_user)
    target_id = _target_id(client)
    _restrict(client, target_id, "reports")

    _login(client, registered_user)
    response = client.get(f"/api/v1/reports/url/{scan['id']}")
    assert response.status_code == 403


def test_restriction_does_not_block_viewing_own_scan_history(client, admin_user, registered_user):
    """Restricting 'url' blocks performing new URL scans — it must not also
    block viewing scans the user already made before being restricted."""
    _login(client, registered_user)
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))

    _login(client, admin_user)
    target_id = _target_id(client)
    _restrict(client, target_id, "url")

    _login(client, registered_user)
    response = client.get("/api/v1/url/history")
    assert response.status_code == 200
    assert response.get_json()["total"] >= 1


def test_restriction_check_is_server_side_not_just_frontend(client, admin_user, registered_user):
    """The core requirement: calling the raw API directly (bypassing any UI)
    still gets blocked once restricted."""
    _login(client, admin_user)
    target_id = _target_id(client)
    _restrict(client, target_id, "url")

    _login(client, registered_user)
    response = client.post(
        "/api/v1/url/scan",
        json={"url": "https://example.com"},
        headers={**csrf_header(client), "X-Requested-With": "raw-curl-not-the-ui"},
    )
    assert response.status_code == 403
    assert "restricted" in response.get_json()["error"].lower()
