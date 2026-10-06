import io

import qrcode

from app.extensions import db
from app.models.email_scan import EmailScanHistory
from app.models.qr_scan import QRScanHistory
from app.models.scan import ScanHistory


def _qr_png(content: str) -> bytes:
    img = qrcode.make(content)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# --- Guest URL scan ---


def test_guest_url_scan_works_without_authentication(client):
    response = client.post("/api/v1/guest/url/scan", json={"url": "https://example.com"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["trust_score"] == 100
    assert body["risk"] == "Safe"
    assert body["persisted"] is False


def test_guest_url_scan_uses_the_same_detection_engine(client, app):
    """Same rule set, same score, as the authenticated path for an
    identical URL -- proves no second/simplified engine was introduced."""
    with app.app_context():
        from app.services.url_scanner.engine import scan_url

        direct_report = scan_url("https://example.com")

    response = client.post("/api/v1/guest/url/scan", json={"url": "https://example.com"})
    body = response.get_json()
    assert body["trust_score"] == direct_report.trust_score
    assert body["risk"] == direct_report.risk_level
    assert {r["rule"] for r in body["rules"]} == {r.rule for r in direct_report.rule_results}


def test_guest_url_scan_preserves_threat_intel_rule_presence(client):
    response = client.post("/api/v1/guest/url/scan", json={"url": "https://example.com"})
    body = response.get_json()
    assert any(r["rule"] == "external_threat_intel" for r in body["rules"])


def test_guest_url_scan_rejects_malformed_url(client):
    response = client.post("/api/v1/guest/url/scan", json={"url": "not-a-url"})
    assert response.status_code == 422


def test_guest_url_scan_is_not_saved_to_any_history(client, app):
    client.post("/api/v1/guest/url/scan", json={"url": "https://example.com"})
    with app.app_context():
        assert ScanHistory.query.count() == 0


def test_guest_url_scan_does_not_appear_in_a_registered_users_history(client, app, registered_user):
    client.post("/api/v1/auth/login", json={"email": registered_user["email"], "password": registered_user["password"]})
    client.post("/api/v1/guest/url/scan", json={"url": "https://example.com"})

    history = client.get("/api/v1/url/history").get_json()
    assert history["total"] == 0


# --- Guest email scan ---


def test_guest_email_scan_works_without_authentication(client):
    response = client.post(
        "/api/v1/guest/email/scan",
        data={"email_text": "From: a@example.com\nSubject: Hi\n\nJust checking in."},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert "trust_score" in body
    assert body["persisted"] is False


def test_guest_email_scan_rejects_missing_input(client):
    response = client.post("/api/v1/guest/email/scan", data={"email_text": ""})
    assert response.status_code == 422


def test_guest_email_scan_is_not_saved_to_any_history(client, app):
    client.post(
        "/api/v1/guest/email/scan",
        data={"email_text": "From: a@example.com\nSubject: Hi\n\nJust checking in."},
    )
    with app.app_context():
        assert EmailScanHistory.query.count() == 0


# --- Guest QR scan ---


def test_guest_qr_scan_works_without_authentication(client):
    response = client.post(
        "/api/v1/guest/qr/scan", data={"qr_image": (io.BytesIO(_qr_png("https://example.com")), "qr.png")}
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["raw_content"] == "https://example.com"
    assert body["persisted"] is False


def test_guest_qr_scan_requires_file(client):
    response = client.post("/api/v1/guest/qr/scan", data={})
    assert response.status_code == 422


def test_guest_qr_scan_is_not_saved_to_any_history(client, app):
    client.post("/api/v1/guest/qr/scan", data={"qr_image": (io.BytesIO(_qr_png("hello")), "qr.png")})
    with app.app_context():
        assert QRScanHistory.query.count() == 0


# --- Guest cannot reach protected data ---


def test_guest_cannot_access_url_history(client):
    assert client.get("/api/v1/url/history").status_code == 401


def test_guest_cannot_access_email_history(client):
    assert client.get("/api/v1/email/history").status_code == 401


def test_guest_cannot_access_qr_history(client):
    assert client.get("/api/v1/qr/history").status_code == 401


def test_guest_cannot_access_profile(client):
    assert client.get("/api/v1/profile").status_code == 401


def test_guest_cannot_access_admin_routes(client):
    assert client.get("/api/v1/admin/users").status_code == 401
    assert client.get("/api/v1/admin/rules").status_code == 401
    assert client.get("/api/v1/admin/system/health").status_code == 401
