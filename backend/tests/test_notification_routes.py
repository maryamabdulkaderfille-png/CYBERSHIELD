import io

from tests.conftest import csrf_header

PHISHING_EML = b"""From: "PayPal Support" <support@mail-secure-paypal.com>
Subject: Urgent: Your Account Will Be Suspended

Dear Customer, verify your identity immediately or your account will be suspended.
http://paypa1-secure-login.com/verify
"""


def _login(client, registered_user):
    client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )


def _trigger_dangerous_url_notification(client):
    return client.post(
        "/api/v1/url/scan",
        json={"url": "http://8.8.8.8/login-verify-secure-bank-wallet"},
        headers=csrf_header(client),
    )


def test_list_requires_auth(client):
    assert client.get("/api/v1/notifications").status_code == 401


def test_list_empty_initially(client, registered_user):
    _login(client, registered_user)
    response = client.get("/api/v1/notifications")
    assert response.status_code == 200
    body = response.get_json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["unread_count"] == 0


def test_dangerous_url_scan_creates_notification(client, registered_user):
    _login(client, registered_user)
    _trigger_dangerous_url_notification(client)

    response = client.get("/api/v1/notifications")
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["type"] == "high_risk_url"
    assert body["unread_count"] == 1


def test_safe_url_scan_does_not_create_notification(client, registered_user):
    _login(client, registered_user)
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))

    response = client.get("/api/v1/notifications")
    assert response.get_json()["total"] == 0


def test_dangerous_email_scan_creates_notification(client, registered_user):
    _login(client, registered_user)
    client.post(
        "/api/v1/email/scan",
        data={"email_file": (io.BytesIO(PHISHING_EML), "phish.eml")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )

    response = client.get("/api/v1/notifications")
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["type"] == "dangerous_email"


def test_unread_count_endpoint(client, registered_user):
    _login(client, registered_user)
    _trigger_dangerous_url_notification(client)

    response = client.get("/api/v1/notifications/unread-count")
    assert response.get_json()["unread_count"] == 1


def test_mark_read(client, registered_user):
    _login(client, registered_user)
    _trigger_dangerous_url_notification(client)
    notification_id = client.get("/api/v1/notifications").get_json()["items"][0]["id"]

    response = client.put(f"/api/v1/notifications/{notification_id}/read", headers=csrf_header(client))
    assert response.status_code == 200
    assert response.get_json()["notification"]["is_read"] is True
    assert client.get("/api/v1/notifications/unread-count").get_json()["unread_count"] == 0


def test_mark_read_nonexistent_returns_404(client, registered_user):
    _login(client, registered_user)
    response = client.put("/api/v1/notifications/99999/read", headers=csrf_header(client))
    assert response.status_code == 404


def test_mark_all_read(client, registered_user):
    _login(client, registered_user)
    _trigger_dangerous_url_notification(client)
    client.post(
        "/api/v1/email/scan",
        data={"email_file": (io.BytesIO(PHISHING_EML), "phish.eml")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )

    response = client.put("/api/v1/notifications/read-all", headers=csrf_header(client))
    assert response.status_code == 200
    assert response.get_json()["updated_count"] == 2
    assert client.get("/api/v1/notifications/unread-count").get_json()["unread_count"] == 0


def test_delete_notification(client, registered_user):
    _login(client, registered_user)
    _trigger_dangerous_url_notification(client)
    notification_id = client.get("/api/v1/notifications").get_json()["items"][0]["id"]

    response = client.delete(f"/api/v1/notifications/{notification_id}", headers=csrf_header(client))
    assert response.status_code == 200
    assert client.get("/api/v1/notifications").get_json()["total"] == 0


def test_delete_nonexistent_returns_404(client, registered_user):
    _login(client, registered_user)
    response = client.delete("/api/v1/notifications/99999", headers=csrf_header(client))
    assert response.status_code == 404


def test_cannot_read_other_users_notification(client, registered_user):
    _login(client, registered_user)
    _trigger_dangerous_url_notification(client)
    notification_id = client.get("/api/v1/notifications").get_json()["items"][0]["id"]
    client.post("/api/v1/auth/logout", headers=csrf_header(client))

    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Other User",
            "username": "otheruser_notif",
            "email": "other_notif@example.com",
            "password": "StrongPass1!",
            "confirm_password": "StrongPass1!",
        },
    )
    response = client.put(f"/api/v1/notifications/{notification_id}/read", headers=csrf_header(client))
    assert response.status_code == 404


def test_pagination(client, registered_user):
    _login(client, registered_user)
    for i in range(3):
        client.post(
            "/api/v1/url/scan",
            json={"url": f"http://8.8.8.{i}/login-verify-secure-bank-wallet"},
            headers=csrf_header(client),
        )

    response = client.get("/api/v1/notifications?page=1&per_page=2")
    body = response.get_json()
    assert len(body["items"]) == 2
    assert body["total"] == 3
    assert body["total_pages"] == 2


def test_unread_only_filter(client, registered_user):
    _login(client, registered_user)
    _trigger_dangerous_url_notification(client)
    notification_id = client.get("/api/v1/notifications").get_json()["items"][0]["id"]
    client.put(f"/api/v1/notifications/{notification_id}/read", headers=csrf_header(client))

    response = client.get("/api/v1/notifications?unread_only=true")
    assert response.get_json()["total"] == 0
