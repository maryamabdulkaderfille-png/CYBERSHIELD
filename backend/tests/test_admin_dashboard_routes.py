from tests.conftest import csrf_header


def _login(client, user):
    client.post("/api/v1/auth/login", json={"email": user["email"], "password": user["password"]})


def test_overview_requires_admin(client, registered_user):
    _login(client, registered_user)
    assert client.get("/api/v1/admin/dashboard").status_code == 403


def test_overview_shape(client, admin_user):
    _login(client, admin_user)
    response = client.get("/api/v1/admin/dashboard")
    assert response.status_code == 200
    body = response.get_json()
    for key in ("users", "scans", "extension_activity", "notifications_sent", "recent_logins", "system_health"):
        assert key in body
    assert body["users"]["total"] >= 1
    assert body["users"]["admins"] >= 1


def test_overview_reflects_platform_wide_scans_across_users(client, admin_user, app):
    _login(client, admin_user)
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))
    client.post("/api/v1/auth/logout", headers=csrf_header(client))

    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Other User",
            "username": "otheruser_admin",
            "email": "other_admin@example.com",
            "password": "StrongPass1!",
            "confirm_password": "StrongPass1!",
        },
    )
    client.post(
        "/api/v1/url/scan",
        json={"url": "http://8.8.8.8/login-verify-secure-bank-wallet"},
        headers=csrf_header(client),
    )
    client.post("/api/v1/auth/logout", headers=csrf_header(client))

    with app.app_context():
        from app.models.user import User

        admin = User.query.filter_by(email="admin@example.com").first()

    client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "StrongPass1!"})
    response = client.get("/api/v1/admin/dashboard")
    body = response.get_json()
    assert body["scans"]["total_scans"] == 2  # one from each of the two non-admin users
    assert admin is not None  # sanity check the DB lookup itself worked


def test_recent_logins_recorded(client, admin_user):
    _login(client, admin_user)
    response = client.get("/api/v1/admin/dashboard")
    logins = response.get_json()["recent_logins"]
    assert len(logins) >= 1
    assert logins[0]["action"] == "login"
