from tests.conftest import csrf_header


def _login(client, registered_user):
    client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )


def test_update_profile(client, registered_user):
    _login(client, registered_user)
    response = client.put(
        "/api/v1/users/me", json={"full_name": "Jane A. Doe"}, headers=csrf_header(client)
    )
    assert response.status_code == 200
    assert response.get_json()["user"]["full_name"] == "Jane A. Doe"


def test_update_profile_rejects_taken_username(client, registered_user):
    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Other User",
            "username": "otheruser",
            "email": "other@example.com",
            "password": "StrongPass1!",
            "confirm_password": "StrongPass1!",
        },
    )
    _login(client, registered_user)
    response = client.put(
        "/api/v1/users/me", json={"username": "otheruser"}, headers=csrf_header(client)
    )
    assert response.status_code == 409


def test_change_password_requires_current_password(client, registered_user):
    _login(client, registered_user)
    response = client.put(
        "/api/v1/users/me/password",
        json={
            "current_password": "WrongCurrent1!",
            "new_password": "NewStrongPass1!",
            "confirm_new_password": "NewStrongPass1!",
        },
        headers=csrf_header(client),
    )
    assert response.status_code == 401


def test_change_password_success(client, registered_user):
    _login(client, registered_user)
    response = client.put(
        "/api/v1/users/me/password",
        json={
            "current_password": registered_user["password"],
            "new_password": "NewStrongPass1!",
            "confirm_new_password": "NewStrongPass1!",
        },
        headers=csrf_header(client),
    )
    assert response.status_code == 200

    login_with_new = client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": "NewStrongPass1!"},
    )
    assert login_with_new.status_code == 200
