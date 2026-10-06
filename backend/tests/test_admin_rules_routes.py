from tests.conftest import csrf_header


def _login(client, user):
    client.post("/api/v1/auth/login", json={"email": user["email"], "password": user["password"]})


def test_list_requires_admin(client, registered_user):
    _login(client, registered_user)
    assert client.get("/api/v1/admin/rules").status_code == 403


def test_list_rules_seeds_and_returns_all_23(client, admin_user):
    _login(client, admin_user)
    response = client.get("/api/v1/admin/rules")
    assert response.status_code == 200
    items = response.get_json()["items"]
    assert len(items) == 23
    assert all(r["enabled"] for r in items)
    assert all(r["version"] == 1 for r in items)


def test_list_rules_filters_by_category(client, admin_user):
    _login(client, admin_user)
    url_rules = client.get("/api/v1/admin/rules?category=url").get_json()["items"]
    email_rules = client.get("/api/v1/admin/rules?category=email").get_json()["items"]
    assert len(url_rules) == 13
    assert len(email_rules) == 10


def test_list_rules_rejects_unknown_category(client, admin_user):
    _login(client, admin_user)
    response = client.get("/api/v1/admin/rules?category=nonsense")
    assert response.status_code == 422


def _find_rule(items, name):
    return next(r for r in items if r["key"].endswith(name))


def test_disabling_https_check_stops_it_from_running(client, admin_user):
    _login(client, admin_user)
    rules = client.get("/api/v1/admin/rules?category=url").get_json()["items"]
    https_rule = _find_rule(rules, "https_check")

    before = client.post(
        "/api/v1/url/scan", json={"url": "http://example.com"}, headers=csrf_header(client)
    ).get_json()
    assert any(r["rule"] == "https_check" for r in before["rules"])

    response = client.put(
        f"/api/v1/admin/rules/{https_rule['id']}", json={"enabled": False}, headers=csrf_header(client)
    )
    assert response.status_code == 200
    assert response.get_json()["rule"]["enabled"] is False
    assert response.get_json()["rule"]["version"] == 2

    after = client.post(
        "/api/v1/url/scan", json={"url": "http://example.com/again"}, headers=csrf_header(client)
    ).get_json()
    assert not any(r["rule"] == "https_check" for r in after["rules"])
    assert len(after["rules"]) == 12  # one fewer than the normal 13


def test_disabling_a_rule_does_not_affect_other_rules(client, admin_user):
    _login(client, admin_user)
    rules = client.get("/api/v1/admin/rules?category=url").get_json()["items"]
    https_rule = _find_rule(rules, "https_check")
    client.put(f"/api/v1/admin/rules/{https_rule['id']}", json={"enabled": False}, headers=csrf_header(client))

    result = client.post(
        "/api/v1/url/scan",
        json={"url": "http://8.8.8.8/login-verify-secure-bank-wallet"},
        headers=csrf_header(client),
    ).get_json()
    triggered = {r["rule"] for r in result["rules"] if r["triggered"]}
    assert "ip_address" in triggered
    assert "suspicious_keywords" in triggered
    assert "https_check" not in {r["rule"] for r in result["rules"]}  # the disabled rule, confirmed absent


def test_re_enabling_a_rule_restores_it(client, admin_user):
    _login(client, admin_user)
    rules = client.get("/api/v1/admin/rules?category=url").get_json()["items"]
    https_rule = _find_rule(rules, "https_check")
    client.put(f"/api/v1/admin/rules/{https_rule['id']}", json={"enabled": False}, headers=csrf_header(client))
    client.put(f"/api/v1/admin/rules/{https_rule['id']}", json={"enabled": True}, headers=csrf_header(client))

    result = client.post(
        "/api/v1/url/scan", json={"url": "http://example.com"}, headers=csrf_header(client)
    ).get_json()
    assert any(r["rule"] == "https_check" for r in result["rules"])
    assert len(result["rules"]) == 13


def test_toggling_same_state_does_not_bump_version(client, admin_user):
    _login(client, admin_user)
    rules = client.get("/api/v1/admin/rules?category=url").get_json()["items"]
    https_rule = _find_rule(rules, "https_check")
    response = client.put(
        f"/api/v1/admin/rules/{https_rule['id']}", json={"enabled": True}, headers=csrf_header(client)
    )
    assert response.get_json()["rule"]["version"] == 1


def test_disabling_email_rule_affects_email_scans_only(client, admin_user):
    _login(client, admin_user)
    rules = client.get("/api/v1/admin/rules?category=email").get_json()["items"]
    greeting_rule = _find_rule(rules, "greeting_analysis")
    client.put(f"/api/v1/admin/rules/{greeting_rule['id']}", json={"enabled": False}, headers=csrf_header(client))

    email_result = client.post(
        "/api/v1/email/scan",
        data={"email_text": "From: a@example.com\nSubject: Hi\n\nHello there"},
        headers=csrf_header(client),
    ).get_json()
    assert not any(r["rule"] == "greeting_analysis" for r in email_result["rules"])

    url_result = client.post(
        "/api/v1/url/scan", json={"url": "http://example.com"}, headers=csrf_header(client)
    ).get_json()
    assert len(url_result["rules"]) == 13  # unaffected


def test_toggle_rule_404_for_unknown_id(client, admin_user):
    _login(client, admin_user)
    response = client.put("/api/v1/admin/rules/999999", json={"enabled": False}, headers=csrf_header(client))
    assert response.status_code == 404


def test_whitelist_check_and_threat_intel_are_registered(client, admin_user):
    """Both rules actively affect scoring (whitelist_check's +15 bonus,
    external_threat_intel's -100 VirusTotal/URLhaus hit) but were previously
    missing from the admin registry — invisible and untoggleable from the
    admin panel despite being live. This is a regression test for that gap."""
    _login(client, admin_user)
    url_rules = client.get("/api/v1/admin/rules?category=url").get_json()["items"]
    names = {r["key"].rsplit(".", 1)[-1] for r in url_rules}
    assert "whitelist_check" in names
    assert "external_threat_intel" in names


def test_disabling_whitelist_check_removes_its_trust_bonus(client, admin_user):
    _login(client, admin_user)
    rules = client.get("/api/v1/admin/rules?category=url").get_json()["items"]
    whitelist_rule = _find_rule(rules, "whitelist_check")

    before = client.post(
        "/api/v1/url/scan", json={"url": "https://www.google.com"}, headers=csrf_header(client)
    ).get_json()
    assert any(r["rule"] == "whitelist_check" and r["triggered"] for r in before["rules"])

    client.put(
        f"/api/v1/admin/rules/{whitelist_rule['id']}", json={"enabled": False}, headers=csrf_header(client)
    )

    after = client.post(
        "/api/v1/url/scan", json={"url": "https://www.google.com/again"}, headers=csrf_header(client)
    ).get_json()
    assert not any(r["rule"] == "whitelist_check" for r in after["rules"])


def test_rule_change_is_audited(client, admin_user):
    _login(client, admin_user)
    rules = client.get("/api/v1/admin/rules?category=url").get_json()["items"]
    https_rule = _find_rule(rules, "https_check")
    client.put(f"/api/v1/admin/rules/{https_rule['id']}", json={"enabled": False}, headers=csrf_header(client))

    logs = client.get("/api/v1/admin/audit-logs?action=rule_change").get_json()["items"]
    assert len(logs) == 1
    assert logs[0]["details"]["enabled"] is False
