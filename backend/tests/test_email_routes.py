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


def test_scan_requires_auth(client):
    response = client.post("/api/v1/email/scan", data={"email_text": "hello"})
    assert response.status_code == 401


def test_scan_with_pasted_text(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/email/scan",
        data={"email_text": "From: a@example.com\nSubject: Hi\n\nJust checking in."},
        headers=csrf_header(client),
    )
    assert response.status_code == 201
    body = response.get_json()
    assert "trust_score" in body
    assert body["sender_email"] == "a@example.com"
    assert body["subject"] == "Hi"


def test_scan_rejects_empty_text(client, registered_user):
    _login(client, registered_user)
    response = client.post("/api/v1/email/scan", data={"email_text": ""}, headers=csrf_header(client))
    assert response.status_code == 422


def test_scan_rejects_neither_text_nor_file(client, registered_user):
    _login(client, registered_user)
    response = client.post("/api/v1/email/scan", data={}, headers=csrf_header(client))
    assert response.status_code == 422


def test_scan_rejects_both_text_and_file(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/email/scan",
        data={
            "email_text": "From: a@example.com\n\nHi",
            "email_file": (io.BytesIO(PHISHING_EML), "test.eml"),
        },
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )
    assert response.status_code == 422


def test_scan_rejects_excessively_long_text(client, registered_user):
    _login(client, registered_user)
    huge_text = "From: a@example.com\n\n" + ("a" * 250_000)
    response = client.post("/api/v1/email/scan", data={"email_text": huge_text}, headers=csrf_header(client))
    assert response.status_code == 422


def test_scan_rejects_control_characters_in_text(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/email/scan",
        data={"email_text": "From: a@example.com\n\nHello\x00world"},
        headers=csrf_header(client),
    )
    assert response.status_code == 422


def test_scan_with_eml_upload(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/email/scan",
        data={"email_file": (io.BytesIO(PHISHING_EML), "phish.eml")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["risk"] == "Dangerous"
    assert body["sender_email"] == "support@mail-secure-paypal.com"


def test_scan_rejects_unsupported_file_extension(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/email/scan",
        data={"email_file": (io.BytesIO(b"not an email"), "malware.exe")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )
    assert response.status_code == 422


def test_scan_msg_upload_returns_clean_not_implemented_error(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/email/scan",
        data={"email_file": (io.BytesIO(b"fake msg content"), "email.msg")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )
    assert response.status_code == 422
    assert "not yet supported" in response.get_json()["error"]


def test_scan_rejects_empty_file(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/email/scan",
        data={"email_file": (io.BytesIO(b""), "empty.eml")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )
    assert response.status_code == 422


def test_scan_rejects_oversized_file(client, registered_user):
    _login(client, registered_user)
    huge_content = b"a" * (6 * 1024 * 1024)
    response = client.post(
        "/api/v1/email/scan",
        data={"email_file": (io.BytesIO(huge_content), "huge.eml")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )
    assert response.status_code in {413, 422}


def test_scan_is_persisted_and_appears_in_history(client, registered_user):
    _login(client, registered_user)
    client.post(
        "/api/v1/email/scan",
        data={"email_file": (io.BytesIO(PHISHING_EML), "phish.eml")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )

    response = client.get("/api/v1/email/history")
    assert response.status_code == 200
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["sender_email"] == "support@mail-secure-paypal.com"


def test_history_requires_auth(client):
    response = client.get("/api/v1/email/history")
    assert response.status_code == 401


def test_history_search_by_sender(client, registered_user):
    _login(client, registered_user)
    client.post(
        "/api/v1/email/scan",
        data={"email_text": "From: alice@example.com\nSubject: Hi\n\nHello"},
        headers=csrf_header(client),
    )
    client.post(
        "/api/v1/email/scan",
        data={"email_text": "From: bob@example.com\nSubject: Hi\n\nHello"},
        headers=csrf_header(client),
    )

    response = client.get("/api/v1/email/history?search=alice")
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["sender_email"] == "alice@example.com"


def test_history_search_by_subject(client, registered_user):
    _login(client, registered_user)
    client.post(
        "/api/v1/email/scan",
        data={"email_text": "From: a@example.com\nSubject: Quarterly Report\n\nHello"},
        headers=csrf_header(client),
    )

    response = client.get("/api/v1/email/history?search=Quarterly")
    body = response.get_json()
    assert body["total"] == 1


def test_history_filters_by_risk_level(client, registered_user):
    _login(client, registered_user)
    client.post(
        "/api/v1/email/scan",
        data={"email_file": (io.BytesIO(PHISHING_EML), "phish.eml")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )
    client.post(
        "/api/v1/email/scan",
        data={"email_text": "From: jane@example.com\nSubject: Hi\n\nJust checking in, thanks!"},
        headers=csrf_header(client),
    )

    response = client.get("/api/v1/email/history?risk_level=Dangerous")
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["risk_level"] == "Dangerous"


def test_history_pagination(client, registered_user):
    _login(client, registered_user)
    for i in range(5):
        client.post(
            "/api/v1/email/scan",
            data={"email_text": f"From: a@example.com\nSubject: Hi {i}\n\nHello"},
            headers=csrf_header(client),
        )

    response = client.get("/api/v1/email/history?page=1&per_page=2")
    body = response.get_json()
    assert len(body["items"]) == 2
    assert body["total"] == 5
    assert body["total_pages"] == 3


def test_scan_detail_endpoint(client, registered_user):
    _login(client, registered_user)
    created = client.post(
        "/api/v1/email/scan",
        data={"email_text": "From: a@example.com\nSubject: Hi\n\nHello"},
        headers=csrf_header(client),
    ).get_json()

    response = client.get(f"/api/v1/email/history/{created['id']}")
    assert response.status_code == 200
    assert response.get_json()["sender_email"] == "a@example.com"


def test_scan_detail_not_found_for_other_users_scan(client, registered_user):
    _login(client, registered_user)
    created = client.post(
        "/api/v1/email/scan",
        data={"email_text": "From: a@example.com\nSubject: Hi\n\nHello"},
        headers=csrf_header(client),
    ).get_json()
    client.post("/api/v1/auth/logout", headers=csrf_header(client))

    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Other User",
            "username": "otheruser2",
            "email": "other2@example.com",
            "password": "StrongPass1!",
            "confirm_password": "StrongPass1!",
        },
    )
    response = client.get(f"/api/v1/email/history/{created['id']}")
    assert response.status_code == 404


def test_stats_endpoint_aggregates_scans(client, registered_user):
    _login(client, registered_user)
    client.post(
        "/api/v1/email/scan",
        data={"email_file": (io.BytesIO(PHISHING_EML), "phish.eml")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )
    client.post(
        "/api/v1/email/scan",
        data={"email_text": "From: jane@example.com\nSubject: Hi\n\nJust checking in, thanks!"},
        headers=csrf_header(client),
    )

    response = client.get("/api/v1/email/stats")
    assert response.status_code == 200
    body = response.get_json()
    assert body["total_emails_scanned"] == 2
    assert body["safe_count"] + body["low_risk_count"] + body["suspicious_count"] + body["dangerous_count"] == 2
    assert len(body["recent_scans"]) == 2
    assert body["average_trust_score"] is not None
