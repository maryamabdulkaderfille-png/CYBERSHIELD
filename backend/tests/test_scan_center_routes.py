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


def _create_one_of_each(client):
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))
    client.post(
        "/api/v1/email/scan",
        data={"email_text": "From: a@example.com\nSubject: Hi\n\nHello"},
        headers=csrf_header(client),
    )
    client.post(
        "/api/v1/qr/scan",
        data={"qr_image": (io.BytesIO(_qr_png("https://example.com")), "qr.png")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    )


def test_list_requires_auth(client):
    assert client.get("/api/v1/scans").status_code == 401


def test_list_combines_all_three_scanner_types(client, registered_user):
    _login(client, registered_user)
    _create_one_of_each(client)

    response = client.get("/api/v1/scans")
    assert response.status_code == 200
    body = response.get_json()
    assert body["total"] == 3
    types_seen = {item["scanner_type"] for item in body["items"]}
    assert types_seen == {"url", "email", "qr"}


def test_list_filters_by_scanner_type(client, registered_user):
    _login(client, registered_user)
    _create_one_of_each(client)

    response = client.get("/api/v1/scans?scanner_type=email")
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["scanner_type"] == "email"


def test_list_filters_by_risk_level(client, registered_user):
    _login(client, registered_user)
    client.post(
        "/api/v1/url/scan",
        json={"url": "http://8.8.8.8/login-verify-secure-bank-wallet"},
        headers=csrf_header(client),
    )
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))

    response = client.get("/api/v1/scans?risk_level=Dangerous")
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["risk_level"] == "Dangerous"


def test_list_filters_by_trust_score_range(client, registered_user):
    _login(client, registered_user)
    _create_one_of_each(client)

    response = client.get("/api/v1/scans?trust_score_min=99&trust_score_max=100")
    body = response.get_json()
    assert body["total"] == 3  # all three are clean/Safe examples


def test_list_search_matches_target(client, registered_user):
    _login(client, registered_user)
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))
    client.post(
        "/api/v1/email/scan",
        data={"email_text": "From: a@example.com\nSubject: Quarterly Report\n\nHi"},
        headers=csrf_header(client),
    )

    response = client.get("/api/v1/scans?search=Quarterly")
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["scanner_type"] == "email"


def test_list_sort_by_trust_score(client, registered_user):
    _login(client, registered_user)
    client.post(
        "/api/v1/url/scan",
        json={"url": "http://8.8.8.8/login-verify-secure-bank-wallet"},
        headers=csrf_header(client),
    )
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))

    response = client.get("/api/v1/scans?sort_by=trust_score&sort_dir=asc")
    body = response.get_json()
    scores = [item["trust_score"] for item in body["items"]]
    assert scores == sorted(scores)


def test_list_pagination(client, registered_user):
    _login(client, registered_user)
    for i in range(5):
        client.post(
            "/api/v1/url/scan", json={"url": f"https://example.com/{i}"}, headers=csrf_header(client)
        )

    response = client.get("/api/v1/scans?page=1&per_page=2")
    body = response.get_json()
    assert len(body["items"]) == 2
    assert body["total"] == 5
    assert body["total_pages"] == 3


def test_get_detail_dispatches_to_correct_scanner(client, registered_user):
    _login(client, registered_user)
    created = client.post(
        "/api/v1/email/scan",
        data={"email_text": "From: a@example.com\nSubject: Hi\n\nHello"},
        headers=csrf_header(client),
    ).get_json()

    response = client.get(f"/api/v1/scans/email/{created['id']}")
    assert response.status_code == 200
    assert response.get_json()["sender_email"] == "a@example.com"


def test_get_detail_not_found_for_other_users_scan(client, registered_user):
    _login(client, registered_user)
    created = client.post(
        "/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client)
    ).get_json()
    client.post("/api/v1/auth/logout", headers=csrf_header(client))

    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Other User",
            "username": "otheruser4",
            "email": "other4@example.com",
            "password": "StrongPass1!",
            "confirm_password": "StrongPass1!",
        },
    )
    response = client.get(f"/api/v1/scans/url/{created['id']}")
    assert response.status_code == 404


def test_delete_single_scan(client, registered_user):
    _login(client, registered_user)
    created = client.post(
        "/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client)
    ).get_json()

    response = client.delete(f"/api/v1/scans/url/{created['id']}", headers=csrf_header(client))
    assert response.status_code == 200

    assert client.get("/api/v1/scans").get_json()["total"] == 0


def test_delete_nonexistent_scan_returns_404(client, registered_user):
    _login(client, registered_user)
    response = client.delete("/api/v1/scans/url/99999", headers=csrf_header(client))
    assert response.status_code == 404


def test_delete_cannot_delete_other_users_scan(client, registered_user):
    _login(client, registered_user)
    created = client.post(
        "/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client)
    ).get_json()
    client.post("/api/v1/auth/logout", headers=csrf_header(client))

    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Other User",
            "username": "otheruser5",
            "email": "other5@example.com",
            "password": "StrongPass1!",
            "confirm_password": "StrongPass1!",
        },
    )
    response = client.delete(f"/api/v1/scans/url/{created['id']}", headers=csrf_header(client))
    assert response.status_code == 404


def test_bulk_delete(client, registered_user):
    _login(client, registered_user)
    _create_one_of_each(client)

    scans = client.get("/api/v1/scans").get_json()["items"]
    items = [{"scanner_type": s["scanner_type"], "id": s["id"]} for s in scans]

    response = client.post(
        "/api/v1/scans/bulk-delete", json={"items": items}, headers=csrf_header(client)
    )
    assert response.status_code == 200
    assert response.get_json()["deleted_count"] == 3
    assert client.get("/api/v1/scans").get_json()["total"] == 0


def test_bulk_delete_rejects_invalid_scanner_type(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/scans/bulk-delete",
        json={"items": [{"scanner_type": "invalid", "id": 1}]},
        headers=csrf_header(client),
    )
    assert response.status_code == 422


def test_stats_endpoint_aggregates_across_types(client, registered_user):
    _login(client, registered_user)
    _create_one_of_each(client)

    response = client.get("/api/v1/scans/stats")
    assert response.status_code == 200
    body = response.get_json()
    assert body["total_scans"] == 3
    assert body["by_scanner_type"] == {"url": 1, "email": 1, "qr": 1}
    assert len(body["recent_scans"]) == 3
    assert body["average_trust_score"] is not None


def test_stats_latest_threats_and_top_risks(client, registered_user):
    _login(client, registered_user)
    client.post(
        "/api/v1/url/scan",
        json={"url": "http://8.8.8.8/login-verify-secure-bank-wallet"},
        headers=csrf_header(client),
    )
    client.post("/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client))

    response = client.get("/api/v1/scans/stats")
    body = response.get_json()
    assert len(body["latest_threats"]) == 1
    assert body["latest_threats"][0]["risk_level"] == "Dangerous"
    assert body["top_risks"][0]["trust_score"] <= body["top_risks"][-1]["trust_score"]
