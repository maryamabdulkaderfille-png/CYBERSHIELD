from tests.conftest import csrf_header


def _login(client, user):
    client.post("/api/v1/auth/login", json={"email": user["email"], "password": user["password"]})


def _register_and_login(client, email="second@example.com", username="seconduser"):
    payload = {
        "full_name": "Second User",
        "username": username,
        "email": email,
        "password": "StrongPass1!",
        "confirm_password": "StrongPass1!",
    }
    client.post("/api/v1/auth/register", json=payload)
    _login(client, payload)
    return payload


def _block(client, target="evil.example", trust_score=8, risk_level="Dangerous", reasons=None):
    return client.post(
        "/api/v1/protection/blocklist",
        json={"target": target, "trust_score": trust_score, "risk_level": risk_level, "reasons": reasons or ["Newly registered domain"]},
        headers=csrf_header(client),
    )


# --- auth required ------------------------------------------------------


def test_all_protection_endpoints_require_auth(client):
    assert client.get("/api/v1/protection/blocklist").status_code == 401
    assert client.post("/api/v1/protection/blocklist", json={}).status_code == 401
    assert client.delete("/api/v1/protection/blocklist/1").status_code == 401
    assert client.post("/api/v1/protection/blocklist/1/restore").status_code == 401
    assert client.get("/api/v1/protection/blocklist/export").status_code == 401
    assert client.get("/api/v1/protection/stats").status_code == 401
    assert client.get("/api/v1/protection/community?domains=a.com").status_code == 401
    assert client.get("/api/v1/protection/community/top").status_code == 401
    assert client.post("/api/v1/protection/explain", json={}).status_code == 401
    assert client.post("/api/v1/protection/report", json={}).status_code == 401
    assert client.get("/api/v1/protection/sync").status_code == 401
    assert client.post("/api/v1/protection/extension-blocked-event", json={}).status_code == 401


# --- Feature 1/2: block / list / unblock / restore ----------------------


def test_block_website_creates_and_returns_entry(client, registered_user):
    _login(client, registered_user)
    response = _block(client)
    assert response.status_code == 201
    body = response.get_json()
    assert body["entry"]["domain"] == "evil.example"
    assert body["entry"]["is_active"] is True


def test_block_website_rejects_duplicate(client, registered_user):
    _login(client, registered_user)
    _block(client)
    response = _block(client)
    assert response.status_code == 409


def test_block_website_rejects_localhost(client, registered_user):
    _login(client, registered_user)
    response = _block(client, target="localhost")
    assert response.status_code == 422


def test_block_website_rejects_private_ip(client, registered_user):
    _login(client, registered_user)
    response = _block(client, target="192.168.1.1")
    assert response.status_code == 422


def test_block_website_validates_risk_level(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/protection/blocklist",
        json={"target": "evil.example", "trust_score": 8, "risk_level": "Not A Real Level", "reasons": []},
        headers=csrf_header(client),
    )
    assert response.status_code == 422


def test_list_blocklist_returns_created_entry(client, registered_user):
    _login(client, registered_user)
    _block(client)
    response = client.get("/api/v1/protection/blocklist")
    assert response.status_code == 200
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["domain"] == "evil.example"


def test_unblock_then_list_removed(client, registered_user):
    _login(client, registered_user)
    entry_id = _block(client).get_json()["entry"]["id"]

    response = client.delete(f"/api/v1/protection/blocklist/{entry_id}", headers=csrf_header(client))
    assert response.status_code == 200
    assert response.get_json()["entry"]["is_active"] is False

    active = client.get("/api/v1/protection/blocklist?is_active=true").get_json()
    removed = client.get("/api/v1/protection/blocklist?is_active=false").get_json()
    assert active["total"] == 0
    assert removed["total"] == 1


def test_restore_reactivates_entry(client, registered_user):
    _login(client, registered_user)
    entry_id = _block(client).get_json()["entry"]["id"]
    client.delete(f"/api/v1/protection/blocklist/{entry_id}", headers=csrf_header(client))

    response = client.post(f"/api/v1/protection/blocklist/{entry_id}/restore", headers=csrf_header(client))
    assert response.status_code == 200
    assert response.get_json()["entry"]["is_active"] is True


def test_user_cannot_unblock_another_users_entry(client, registered_user):
    _login(client, registered_user)
    entry_id = _block(client).get_json()["entry"]["id"]
    client.post("/api/v1/auth/logout", headers=csrf_header(client))

    _register_and_login(client)
    response = client.delete(f"/api/v1/protection/blocklist/{entry_id}", headers=csrf_header(client))
    assert response.status_code == 404


def test_export_json_and_csv(client, registered_user):
    _login(client, registered_user)
    _block(client)

    json_response = client.get("/api/v1/protection/blocklist/export?format=json")
    assert json_response.status_code == 200
    assert json_response.get_json()["items"][0]["domain"] == "evil.example"

    csv_response = client.get("/api/v1/protection/blocklist/export?format=csv")
    assert csv_response.status_code == 200
    assert csv_response.mimetype == "text/csv"
    assert b"evil.example" in csv_response.data


def test_export_rejects_unsupported_format(client, registered_user):
    _login(client, registered_user)
    response = client.get("/api/v1/protection/blocklist/export?format=xml")
    assert response.status_code == 422


# --- Feature 5: protection stats -----------------------------------------


def test_protection_stats_reflect_a_block(client, registered_user):
    _login(client, registered_user)
    _block(client)
    response = client.get("/api/v1/protection/stats")
    assert response.status_code == 200
    body = response.get_json()
    assert body["total_blocked_domains"] == 1
    assert body["blocked_today"] == 1
    assert len(body["recent_blocked"]) == 1


# --- Feature 8: community intelligence -----------------------------------


def test_community_intel_reflects_multiple_users(client, registered_user):
    _login(client, registered_user)
    _block(client, target="shared.example")

    _register_and_login(client)
    _block(client, target="shared.example")

    response = client.get("/api/v1/protection/community?domains=shared.example")
    assert response.status_code == 200
    intel = response.get_json()["items"]["shared.example"]
    assert intel["blocked_by_users"] == 2


# --- Feature 7: explanation -----------------------------------------------


def test_explain_endpoint_returns_templated_explanation(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/protection/explain",
        json={
            "risk": "Dangerous",
            "trust_score": 5,
            "reasons": ["Fake login page"],
            "rules": [{"rule": "ip_address", "triggered": True, "severity": "high", "message": "Raw IP address used as host"}],
        },
        headers=csrf_header(client),
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["risk"] == "Dangerous"
    assert "Raw IP address used as host" in body["points"]


# --- report website (Feature 1) -------------------------------------------


def test_report_website_creates_audit_entry(client, admin_user, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/protection/report", json={"target": "https://evil.example/login", "reasons": ["fake"]}, headers=csrf_header(client)
    )
    assert response.status_code == 201
    assert "evil.example" in response.get_json()["message"]


# --- extension sync + enforcement events (Feature 3/9) --------------------


def test_sync_returns_blocked_domains_and_protection_mode(client, registered_user):
    _login(client, registered_user)
    _block(client)
    response = client.get("/api/v1/protection/sync")
    assert response.status_code == 200
    body = response.get_json()
    assert body["protection_mode"] == "warn_only"
    assert body["blocked_domains"][0]["domain"] == "evil.example"
    assert body["blocked_domains"][0]["scan_id"] is None


def test_extension_blocked_event_is_recorded(client, registered_user):
    _login(client, registered_user)
    response = client.post(
        "/api/v1/protection/extension-blocked-event", json={"domain": "evil.example"}, headers=csrf_header(client)
    )
    assert response.status_code == 201

    notifications = client.get("/api/v1/notifications").get_json()["items"]
    assert any(n["type"] == "extension_blocked_access" for n in notifications)


# --- Feature 4: protection mode setting ------------------------------------


def test_updating_protection_mode_persists_and_notifies(client, registered_user):
    _login(client, registered_user)
    response = client.put(
        "/api/v1/settings", json={"protection_mode": "auto_block_dangerous"}, headers=csrf_header(client)
    )
    assert response.status_code == 200
    assert response.get_json()["settings"]["protection_mode"] == "auto_block_dangerous"

    notifications = client.get("/api/v1/notifications").get_json()["items"]
    assert any(n["type"] == "protection_mode_changed" for n in notifications)


def test_protection_mode_rejects_invalid_value(client, registered_user):
    _login(client, registered_user)
    response = client.put("/api/v1/settings", json={"protection_mode": "not-a-real-mode"}, headers=csrf_header(client))
    assert response.status_code == 422


# --- Feature 9: community threat alert wired into the URL scan route ------


def test_scanning_a_domain_blocked_by_many_others_triggers_community_alert(client, app, registered_user):
    from app.extensions import db
    from app.models.blacklist import BlacklistEntry

    with app.app_context():
        db.session.add(BlacklistEntry(domain="known-phish.example", reason="Reported phishing site"))
        db.session.commit()

    # Three other users block the domain first, to cross the alert threshold.
    for i in range(3):
        _register_and_login(client, email=f"other{i}@example.com", username=f"other{i}")
        _block(client, target="known-phish.example")
        client.post("/api/v1/auth/logout", headers=csrf_header(client))

    _login(client, registered_user)
    scan_response = client.post(
        "/api/v1/url/scan", json={"url": "https://known-phish.example/login"}, headers=csrf_header(client)
    )
    assert scan_response.get_json()["risk"] == "Dangerous"

    notifications = client.get("/api/v1/notifications").get_json()["items"]
    assert any(n["type"] == "community_threat_alert" for n in notifications)
