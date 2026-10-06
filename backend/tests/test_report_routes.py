from tests.conftest import csrf_header


def _login(client, registered_user):
    client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )


def test_report_requires_auth(client):
    assert client.get("/api/v1/reports/url/1").status_code == 401


def test_report_rejects_unknown_scanner_type(client, registered_user):
    _login(client, registered_user)
    response = client.get("/api/v1/reports/carrier-pigeon/1")
    assert response.status_code == 422


def test_report_not_found(client, registered_user):
    _login(client, registered_user)
    response = client.get("/api/v1/reports/url/99999")
    assert response.status_code == 404


def test_report_for_url_scan(client, registered_user):
    _login(client, registered_user)
    created = client.post(
        "/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client)
    ).get_json()

    response = client.get(f"/api/v1/reports/url/{created['id']}")
    assert response.status_code == 200
    body = response.get_json()
    assert body["report_id"] == f"url-{created['id']}"
    assert body["scanner_type"] == "url"
    assert body["target"] == "https://example.com"
    assert "example.com" in body["summary"]
    assert body["user"]["email"] == registered_user["email"]
    assert "reasons" in body["findings"]
    assert "rules" in body["findings"]
    assert isinstance(body["recommendations"], list)
    assert body["raw"]["url"] == "https://example.com"


def test_report_for_email_scan(client, registered_user):
    _login(client, registered_user)
    created = client.post(
        "/api/v1/email/scan",
        data={"email_text": "From: a@example.com\nSubject: Hi\n\nHello"},
        headers=csrf_header(client),
    ).get_json()

    response = client.get(f"/api/v1/reports/email/{created['id']}")
    assert response.status_code == 200
    body = response.get_json()
    assert body["scanner_type"] == "email"
    assert "a@example.com" in body["target"]


def test_report_for_qr_scan(client, registered_user):
    import io

    import qrcode

    _login(client, registered_user)
    img = qrcode.make("https://example.com")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    created = client.post(
        "/api/v1/qr/scan",
        data={"qr_image": (buf, "qr.png")},
        headers=csrf_header(client),
        content_type="multipart/form-data",
    ).get_json()

    response = client.get(f"/api/v1/reports/qr/{created['id']}")
    assert response.status_code == 200
    body = response.get_json()
    assert body["scanner_type"] == "qr"
    assert "qr code" in body["summary"].lower()


def test_report_scoped_to_owning_user(client, registered_user):
    _login(client, registered_user)
    created = client.post(
        "/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client)
    ).get_json()
    client.post("/api/v1/auth/logout", headers=csrf_header(client))

    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Other User",
            "username": "otheruser6",
            "email": "other6@example.com",
            "password": "StrongPass1!",
            "confirm_password": "StrongPass1!",
        },
    )
    response = client.get(f"/api/v1/reports/url/{created['id']}")
    assert response.status_code == 404


def test_export_pdf_returns_valid_pdf_report(client, registered_user):
    """PDF export is fully implemented via PdfReportExporter (ReportLab) —
    this used to assert a 501 placeholder response that no longer matches
    the real implementation (get_exporter("pdf") always returns a working
    exporter; there is no feature-flag/not-implemented branch). Verifies the
    actual contract instead: a real PDF document, correct content type, and
    a correctly named attachment."""
    _login(client, registered_user)
    created = client.post(
        "/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client)
    ).get_json()

    response = client.post(
        f"/api/v1/reports/url/{created['id']}/export",
        json={"format": "pdf"},
        headers=csrf_header(client),
    )

    assert response.status_code == 200
    assert response.content_type == "application/pdf"
    assert response.data.startswith(b"%PDF-")  # real PDF file signature
    assert len(response.data) > 0

    disposition = response.headers["Content-Disposition"]
    assert "attachment" in disposition
    assert f"cybershield-report-url-{created['id']}.pdf" in disposition


def test_export_unknown_format_rejected(client, registered_user):
    _login(client, registered_user)
    created = client.post(
        "/api/v1/url/scan", json={"url": "https://example.com"}, headers=csrf_header(client)
    ).get_json()

    response = client.post(
        f"/api/v1/reports/url/{created['id']}/export",
        json={"format": "docx"},
        headers=csrf_header(client),
    )
    assert response.status_code == 422
