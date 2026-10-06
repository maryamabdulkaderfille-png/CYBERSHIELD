from tests.conftest import csrf_header


def _login(client, registered_user):
    client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )


def test_get_profile_requires_auth(client):
    assert client.get("/api/v1/profile").status_code == 401


def test_get_profile_returns_user_and_stats(client, registered_user):
    _login(client, registered_user)
    response = client.get("/api/v1/profile")
    assert response.status_code == 200
    body = response.get_json()
    assert body["user"]["email"] == registered_user["email"]
    assert body["stats"]["total_scans"] == 0
    assert body["stats"]["security_score"] is None


def test_update_profile_fields(client, registered_user):
    _login(client, registered_user)
    response = client.put(
        "/api/v1/profile",
        json={"phone": "+1 555-123-4567", "country": "us", "bio": "Security enthusiast", "avatar_url": "https://example.com/me.png"},
        headers=csrf_header(client),
    )
    assert response.status_code == 200
    user = response.get_json()["user"]
    assert user["phone"] == "+1 555-123-4567"
    assert user["country"] == "US"  # uppercased
    assert user["bio"] == "Security enthusiast"
    assert user["avatar_url"] == "https://example.com/me.png"


def test_update_profile_rejects_unknown_field(client, registered_user):
    _login(client, registered_user)
    response = client.put(
        "/api/v1/profile",
        json={"role": "admin"},  # mass-assignment attempt
        headers=csrf_header(client),
    )
    assert response.status_code == 422


def test_update_profile_rejects_invalid_country(client, registered_user):
    _login(client, registered_user)
    response = client.put(
        "/api/v1/profile", json={"country": "USA"}, headers=csrf_header(client)
    )
    assert response.status_code == 422


def test_update_profile_rejects_invalid_phone(client, registered_user):
    _login(client, registered_user)
    response = client.put(
        "/api/v1/profile", json={"phone": "not-a-phone-number!!"}, headers=csrf_header(client)
    )
    assert response.status_code == 422


def test_update_profile_rejects_invalid_url(client, registered_user):
    _login(client, registered_user)
    response = client.put(
        "/api/v1/profile", json={"avatar_url": "not a url"}, headers=csrf_header(client)
    )
    assert response.status_code == 422


def test_update_profile_partial_update_preserves_other_fields(client, registered_user):
    _login(client, registered_user)
    client.put("/api/v1/profile", json={"bio": "First bio"}, headers=csrf_header(client))
    response = client.put("/api/v1/profile", json={"phone": "5551234567"}, headers=csrf_header(client))
    user = response.get_json()["user"]
    assert user["bio"] == "First bio"
    assert user["phone"] == "5551234567"


def test_stats_reflect_scan_activity(client, registered_user):
    _login(client, registered_user)
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))

    response = client.get("/api/v1/profile")
    stats = response.get_json()["stats"]
    assert stats["total_scans"] == 1
    assert stats["url_scans"] == 1
    assert stats["safe_scans"] == 1
    assert stats["security_score"] is not None
