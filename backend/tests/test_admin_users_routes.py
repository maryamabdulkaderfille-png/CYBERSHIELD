from tests.conftest import csrf_header


def _login(client, user):
    client.post("/api/v1/auth/login", json={"email": user["email"], "password": user["password"]})


def test_list_users_requires_admin(client, registered_user):
    _login(client, registered_user)
    assert client.get("/api/v1/admin/users").status_code == 403


def test_list_users_includes_registered_users(client, admin_user, registered_user):
    _login(client, admin_user)
    response = client.get("/api/v1/admin/users")
    assert response.status_code == 200
    body = response.get_json()
    emails = {u["email"] for u in body["items"]}
    assert admin_user["email"] in emails
    assert registered_user["email"] in emails


def test_list_users_search_filters(client, admin_user, registered_user):
    _login(client, admin_user)
    response = client.get("/api/v1/admin/users?search=jane")
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["email"] == registered_user["email"]


def test_list_users_filters_by_role(client, admin_user, registered_user):
    _login(client, admin_user)
    response = client.get("/api/v1/admin/users?role=admin")
    body = response.get_json()
    assert all(u["role"] == "admin" for u in body["items"])


def test_get_user_detail_includes_stats_and_sessions(client, admin_user, registered_user):
    _login(client, admin_user)
    # need the target user's id
    users = client.get("/api/v1/admin/users?search=jane").get_json()["items"]
    target_id = users[0]["id"]

    response = client.get(f"/api/v1/admin/users/{target_id}")
    assert response.status_code == 200
    body = response.get_json()
    assert "user" in body and "stats" in body and "sessions" in body


def test_get_user_detail_404_for_unknown_id(client, admin_user):
    _login(client, admin_user)
    response = client.get("/api/v1/admin/users/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_deactivate_and_reactivate_user(client, admin_user, registered_user):
    _login(client, admin_user)
    users = client.get("/api/v1/admin/users?search=jane").get_json()["items"]
    target_id = users[0]["id"]

    response = client.post(f"/api/v1/admin/users/{target_id}/deactivate", headers=csrf_header(client))
    assert response.status_code == 200
    assert response.get_json()["user"]["is_active"] is False

    # deactivated user can no longer log in
    login_response = client.post(
        "/api/v1/auth/login", json={"email": registered_user["email"], "password": registered_user["password"]}
    )
    assert login_response.status_code == 403

    _login(client, admin_user)
    response = client.post(f"/api/v1/admin/users/{target_id}/reactivate", headers=csrf_header(client))
    assert response.status_code == 200
    assert response.get_json()["user"]["is_active"] is True


def test_admin_cannot_deactivate_own_account(client, admin_user):
    _login(client, admin_user)
    users = client.get("/api/v1/admin/users?search=Ada").get_json()["items"]
    own_id = users[0]["id"]
    response = client.post(f"/api/v1/admin/users/{own_id}/deactivate", headers=csrf_header(client))
    assert response.status_code == 400


def test_reset_password_placeholder_returns_501(client, admin_user, registered_user):
    _login(client, admin_user)
    users = client.get("/api/v1/admin/users?search=jane").get_json()["items"]
    target_id = users[0]["id"]
    response = client.post(f"/api/v1/admin/users/{target_id}/reset-password", headers=csrf_header(client))
    assert response.status_code == 501


def test_deactivate_user_is_audited(client, admin_user, registered_user):
    _login(client, admin_user)
    users = client.get("/api/v1/admin/users?search=jane").get_json()["items"]
    target_id = users[0]["id"]
    client.post(f"/api/v1/admin/users/{target_id}/deactivate", headers=csrf_header(client))

    logs = client.get("/api/v1/admin/audit-logs?action=admin_action").get_json()["items"]
    assert any(log["details"].get("target_user_id") == target_id for log in logs)


# --- Status field (suspend/remove/reactivate) -------------------------------


def test_deactivate_sets_status_to_suspended(client, admin_user, registered_user):
    _login(client, admin_user)
    users = client.get("/api/v1/admin/users?search=jane").get_json()["items"]
    target_id = users[0]["id"]

    response = client.post(f"/api/v1/admin/users/{target_id}/deactivate", headers=csrf_header(client))
    assert response.get_json()["user"]["status"] == "suspended"


def test_status_endpoint_removes_a_user(client, admin_user, registered_user):
    _login(client, admin_user)
    users = client.get("/api/v1/admin/users?search=jane").get_json()["items"]
    target_id = users[0]["id"]

    response = client.patch(
        f"/api/v1/admin/users/{target_id}/status", json={"status": "removed"}, headers=csrf_header(client)
    )
    assert response.status_code == 200
    body = response.get_json()["user"]
    assert body["status"] == "removed"
    assert body["is_active"] is False


def test_status_endpoint_rejects_unknown_status(client, admin_user, registered_user):
    _login(client, admin_user)
    users = client.get("/api/v1/admin/users?search=jane").get_json()["items"]
    target_id = users[0]["id"]

    response = client.patch(
        f"/api/v1/admin/users/{target_id}/status", json={"status": "banned"}, headers=csrf_header(client)
    )
    assert response.status_code == 422


def test_admin_cannot_change_own_status(client, admin_user):
    _login(client, admin_user)
    users = client.get("/api/v1/admin/users?search=Ada").get_json()["items"]
    own_id = users[0]["id"]

    response = client.patch(
        f"/api/v1/admin/users/{own_id}/status", json={"status": "suspended"}, headers=csrf_header(client)
    )
    assert response.status_code == 400


def test_removed_users_are_excluded_from_default_list_but_visible_via_filter(
    client, admin_user, registered_user
):
    _login(client, admin_user)
    users = client.get("/api/v1/admin/users?search=jane").get_json()["items"]
    target_id = users[0]["id"]
    client.patch(f"/api/v1/admin/users/{target_id}/status", json={"status": "removed"}, headers=csrf_header(client))

    default_list = client.get("/api/v1/admin/users?search=jane").get_json()["items"]
    assert not any(u["id"] == target_id for u in default_list)

    removed_list = client.get("/api/v1/admin/users?status=removed&search=jane").get_json()["items"]
    assert any(u["id"] == target_id for u in removed_list)


def test_removed_users_scan_and_audit_history_stay_intact(client, admin_user, registered_user):
    _login(client, admin_user)
    users = client.get("/api/v1/admin/users?search=jane").get_json()["items"]
    target_id = users[0]["id"]

    _login(client, registered_user)
    scan = client.post(
        "/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client)
    ).get_json()

    _login(client, admin_user)
    client.patch(f"/api/v1/admin/users/{target_id}/status", json={"status": "removed"}, headers=csrf_header(client))

    # The scan row (FK'd to the now-removed user) is still reachable via the
    # platform-wide admin scans endpoint — nothing was hard-deleted.
    admin_scans = client.get("/api/v1/admin/scans").get_json()["items"]
    assert any(item["id"] == scan["id"] and item["scanner_type"] == "url" for item in admin_scans)

    # Their audit trail (e.g. the login that happened above) is still queryable.
    logs = client.get(f"/api/v1/admin/audit-logs?user_id={target_id}").get_json()["items"]
    assert len(logs) > 0


def test_suspend_immediately_revokes_existing_sessions(app, client, admin_user, registered_user):
    """A refresh with the target's now-revoked refresh token must fail right
    away — not just future logins. Uses two independent test clients so the
    target's and the admin's cookies never collide on the same jar."""
    target_client = app.test_client()
    login_response = target_client.post(
        "/api/v1/auth/login", json={"email": registered_user["email"], "password": registered_user["password"]}
    )
    assert login_response.status_code == 200

    _login(client, admin_user)
    users = client.get("/api/v1/admin/users?search=jane").get_json()["items"]
    target_id = users[0]["id"]
    client.post(f"/api/v1/admin/users/{target_id}/deactivate", headers=csrf_header(client))

    refresh_response = target_client.post(
        "/api/v1/auth/refresh", headers=csrf_header(target_client, "csrf_refresh_token")
    )
    assert refresh_response.status_code == 401


def test_reactivating_a_suspended_user_restores_status_and_login(client, admin_user, registered_user):
    _login(client, admin_user)
    users = client.get("/api/v1/admin/users?search=jane").get_json()["items"]
    target_id = users[0]["id"]
    client.post(f"/api/v1/admin/users/{target_id}/deactivate", headers=csrf_header(client))

    response = client.post(f"/api/v1/admin/users/{target_id}/reactivate", headers=csrf_header(client))
    assert response.get_json()["user"]["status"] == "active"

    login_response = client.post(
        "/api/v1/auth/login", json={"email": registered_user["email"], "password": registered_user["password"]}
    )
    assert login_response.status_code == 200


def test_status_change_is_audited_with_old_and_new_status(client, admin_user, registered_user):
    _login(client, admin_user)
    users = client.get("/api/v1/admin/users?search=jane").get_json()["items"]
    target_id = users[0]["id"]
    client.patch(f"/api/v1/admin/users/{target_id}/status", json={"status": "removed"}, headers=csrf_header(client))

    logs = client.get("/api/v1/admin/audit-logs?action=admin_action").get_json()["items"]
    entry = next(log for log in logs if log["details"].get("action_detail") == "user_status_change")
    assert entry["details"]["old_status"] == "active"
    assert entry["details"]["new_status"] == "removed"
    assert entry["details"]["target_user_id"] == target_id
