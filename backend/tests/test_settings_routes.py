from tests.conftest import csrf_header


def _login(client, registered_user):
    client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )


def test_get_settings_requires_auth(client):
    assert client.get("/api/v1/settings").status_code == 401


def test_get_settings_creates_defaults_on_first_access(client, registered_user):
    _login(client, registered_user)
    response = client.get("/api/v1/settings")
    assert response.status_code == 200
    settings = response.get_json()["settings"]
    assert settings["theme"] == "system"
    assert settings["language"] == "en"
    assert settings["timezone"] == "UTC"
    assert settings["notify_high_risk_url"] is True
    assert settings["profile_visibility"] == "private"


def test_update_settings(client, registered_user):
    _login(client, registered_user)
    response = client.put(
        "/api/v1/settings",
        json={"theme": "dark", "timezone": "America/New_York", "notify_qr_threat": False},
        headers=csrf_header(client),
    )
    assert response.status_code == 200
    settings = response.get_json()["settings"]
    assert settings["theme"] == "dark"
    assert settings["timezone"] == "America/New_York"
    assert settings["notify_qr_threat"] is False

    # persisted
    reloaded = client.get("/api/v1/settings").get_json()["settings"]
    assert reloaded["theme"] == "dark"


def test_update_settings_rejects_invalid_theme(client, registered_user):
    _login(client, registered_user)
    response = client.put("/api/v1/settings", json={"theme": "rainbow"}, headers=csrf_header(client))
    assert response.status_code == 422


def test_update_settings_rejects_invalid_timezone(client, registered_user):
    _login(client, registered_user)
    response = client.put(
        "/api/v1/settings", json={"timezone": "Not/A_Timezone"}, headers=csrf_header(client)
    )
    assert response.status_code == 422


def test_update_settings_rejects_unknown_field(client, registered_user):
    _login(client, registered_user)
    response = client.put(
        "/api/v1/settings", json={"user_id": "someone-elses-id"}, headers=csrf_header(client)
    )
    assert response.status_code == 422


def test_sessions_list_includes_current_session(client, registered_user):
    # registered_user's fixture already logs one session in at registration;
    # _login adds a second — exactly one of the two is "current".
    _login(client, registered_user)
    response = client.get("/api/v1/settings/sessions")
    assert response.status_code == 200
    sessions = response.get_json()["sessions"]
    assert len(sessions) == 2
    current = [s for s in sessions if s["is_current"]]
    assert len(current) == 1
    assert all(s["is_revoked"] is False for s in sessions)


def test_second_login_creates_a_second_session(client, app, registered_user):
    _login(client, registered_user)  # 2 sessions so far (register + login)

    second_client = app.test_client()
    second_client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )

    response = second_client.get("/api/v1/settings/sessions")
    sessions = response.get_json()["sessions"]
    assert len(sessions) == 3
    current = [s for s in sessions if s["is_current"]]
    assert len(current) == 1


def test_revoke_session_by_id(client, registered_user):
    _login(client, registered_user)
    before = client.get("/api/v1/settings/sessions").get_json()["sessions"]
    session_id = before[0]["id"]

    response = client.delete(f"/api/v1/settings/sessions/{session_id}", headers=csrf_header(client))
    assert response.status_code == 200
    after = client.get("/api/v1/settings/sessions").get_json()["sessions"]
    assert len(after) == len(before) - 1
    assert session_id not in {s["id"] for s in after}


def test_revoke_nonexistent_session_returns_404(client, registered_user):
    _login(client, registered_user)
    response = client.delete("/api/v1/settings/sessions/99999", headers=csrf_header(client))
    assert response.status_code == 404


def test_revoke_other_sessions_keeps_current(client, app, registered_user):
    _login(client, registered_user)  # register + login = 2 sessions
    second_client = app.test_client()
    second_client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )  # +1 more = 3 sessions total

    response = client.post("/api/v1/settings/sessions/revoke-others", headers=csrf_header(client))
    assert response.status_code == 200
    assert response.get_json()["revoked_count"] == 2

    remaining = client.get("/api/v1/settings/sessions").get_json()["sessions"]
    assert len(remaining) == 1
    assert remaining[0]["is_current"] is True


def test_deactivate_account_requires_correct_password(client, registered_user):
    _login(client, registered_user)
    response = client.delete(
        "/api/v1/settings/account", json={"password": "WrongPassword1!"}, headers=csrf_header(client)
    )
    assert response.status_code == 401


def test_deactivate_account_success_prevents_future_login(client, registered_user):
    _login(client, registered_user)
    response = client.delete(
        "/api/v1/settings/account",
        json={"password": registered_user["password"]},
        headers=csrf_header(client),
    )
    assert response.status_code == 200

    fresh_client = client
    login_response = fresh_client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    assert login_response.status_code == 403


def test_export_placeholder_returns_501(client, registered_user):
    _login(client, registered_user)
    response = client.get("/api/v1/settings/export")
    assert response.status_code == 501
