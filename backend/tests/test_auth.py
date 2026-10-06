from tests.conftest import csrf_header


def test_register_creates_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Jane Doe",
            "username": "janedoe",
            "email": "jane@example.com",
            "password": "StrongPass1!",
            "confirm_password": "StrongPass1!",
        },
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["user"]["email"] == "jane@example.com"
    assert body["user"]["is_verified"] is False
    assert "access_token" in response.headers.get("Set-Cookie", "")


def test_register_rejects_duplicate_email(client, registered_user):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Someone Else",
            "username": "someoneelse",
            "email": registered_user["email"],
            "password": "StrongPass1!",
            "confirm_password": "StrongPass1!",
        },
    )
    assert response.status_code == 409


def test_register_rejects_weak_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Jane Doe",
            "username": "janedoe2",
            "email": "jane2@example.com",
            "password": "weak",
            "confirm_password": "weak",
        },
    )
    assert response.status_code == 422


def test_register_rejects_mismatched_passwords(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Jane Doe",
            "username": "janedoe3",
            "email": "jane3@example.com",
            "password": "StrongPass1!",
            "confirm_password": "Different1!",
        },
    )
    assert response.status_code == 422


def test_login_success(client, registered_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    assert response.status_code == 200
    assert response.get_json()["user"]["email"] == registered_user["email"]


def test_login_invalid_password(client, registered_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": "WrongPass1!"},
    )
    assert response.status_code == 401


def test_login_unknown_email(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "StrongPass1!"},
    )
    assert response.status_code == 401


def test_protected_route_requires_auth(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_protected_route_with_login(client, registered_user):
    client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    response = client.get("/api/v1/users/me")
    assert response.status_code == 200
    assert response.get_json()["user"]["email"] == registered_user["email"]


def test_logout_revokes_access_token(client, registered_user):
    client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    logout_response = client.post("/api/v1/auth/logout", headers=csrf_header(client))
    assert logout_response.status_code == 200

    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_forgot_password_does_not_leak_account_existence(client):
    known = client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
    assert known.status_code == 200
    assert "reset link has been sent" in known.get_json()["message"]
