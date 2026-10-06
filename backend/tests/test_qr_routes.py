import io

import qrcode

from tests.conftest import csrf_header


def _login(client, registered_user):
    client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )


def _qr_png(content: str) -> bytes:
    img = qrcode.make(content)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_scan_requires_auth(client):
    response = client.post("/api/v1/qr/scan", data={"qr_image": (io.BytesIO(_qr_png("hi")), "qr.png")})
    assert response.status_code == 401


def test_scan_requires_file(client, registered_user):
    _login(client, registered_user)
    response = client.post("/api/v1/qr/scan", data={}, headers=csrf_header(client))
    assert response.status_code == 422


def test_scan_rejects_unsupported_extension(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/qr/scan",
        data={"qr_image": (io.BytesIO(b"not an image"), "file.gif")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )
    assert response.status_code == 422


def test_scan_rejects_empty_file(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/qr/scan",
        data={"qr_image": (io.BytesIO(b""), "empty.png")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )
    assert response.status_code == 422


def test_scan_rejects_malformed_image(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/qr/scan",
        data={"qr_image": (io.BytesIO(b"not a real png despite the extension"), "fake.png")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )
    assert response.status_code == 422


def test_scan_rejects_oversized_file(client, registered_user):
    _login(client, registered_user)
    huge = b"a" * (6 * 1024 * 1024)
    response = client.post(
        "/api/v1/qr/scan",
        data={"qr_image": (io.BytesIO(huge), "huge.png")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )
    assert response.status_code in {413, 422}


def test_scan_rejects_image_with_no_qr_code(client, registered_user):
    from PIL import Image

    _login(client, registered_user)
    blank = Image.new("RGB", (100, 100), color="white")
    buf = io.BytesIO()
    blank.save(buf, format="PNG")
    buf.seek(0)
    response = client.post(
        "/api/v1/qr/scan",
        data={"qr_image": (buf, "blank.png")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )
    assert response.status_code == 422


def test_scan_url_qr_code(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/qr/scan",
        data={"qr_image": (io.BytesIO(_qr_png("https://example.com")), "qr.png")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["content_type"] == "url"
    assert body["risk"] == "Safe"
    assert body["parsed_fields"]["url"] == "https://example.com"


def test_scan_wifi_qr_code_never_returns_password(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/qr/scan",
        data={"qr_image": (io.BytesIO(_qr_png("WIFI:S:Home;T:WPA;P:supersecret123;H:false;;")), "wifi.png")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["content_type"] == "wifi"
    assert "supersecret123" not in response.get_data(as_text=True)


def test_scan_is_persisted_and_appears_in_history(client, registered_user):
    _login(client, registered_user)
    client.post(
        "/api/v1/qr/scan",
        data={"qr_image": (io.BytesIO(_qr_png("https://example.com")), "qr.png")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )

    response = client.get("/api/v1/qr/history")
    assert response.status_code == 200
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["content_type"] == "url"


def test_history_requires_auth(client):
    response = client.get("/api/v1/qr/history")
    assert response.status_code == 401


def test_history_filters_by_risk_level(client, registered_user):
    _login(client, registered_user)
    client.post(
        "/api/v1/qr/scan",
        data={"qr_image": (io.BytesIO(_qr_png("tel:+19005551234")), "phone.png")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )
    client.post(
        "/api/v1/qr/scan",
        data={"qr_image": (io.BytesIO(_qr_png("https://example.com")), "qr.png")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )

    response = client.get("/api/v1/qr/history?risk_level=Dangerous")
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["risk_level"] == "Dangerous"


def test_scan_detail_endpoint(client, registered_user):
    _login(client, registered_user)
    created = client.post(
        "/api/v1/qr/scan",
        data={"qr_image": (io.BytesIO(_qr_png("https://example.com")), "qr.png")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    ).get_json()

    response = client.get(f"/api/v1/qr/history/{created['id']}")
    assert response.status_code == 200
    assert response.get_json()["raw_content"] == "https://example.com"


def test_scan_detail_not_found_for_other_users_scan(client, registered_user):
    _login(client, registered_user)
    created = client.post(
        "/api/v1/qr/scan",
        data={"qr_image": (io.BytesIO(_qr_png("https://example.com")), "qr.png")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    ).get_json()
    client.post("/api/v1/auth/logout", headers=csrf_header(client))

    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Other User",
            "username": "otheruser3",
            "email": "other3@example.com",
            "password": "StrongPass1!",
            "confirm_password": "StrongPass1!",
        },
    )
    response = client.get(f"/api/v1/qr/history/{created['id']}")
    assert response.status_code == 404


def test_stats_endpoint(client, registered_user):
    _login(client, registered_user)
    client.post(
        "/api/v1/qr/scan",
        data={"qr_image": (io.BytesIO(_qr_png("https://example.com")), "qr.png")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )

    response = client.get("/api/v1/qr/stats")
    assert response.status_code == 200
    body = response.get_json()
    assert body["total_qr_scanned"] == 1
