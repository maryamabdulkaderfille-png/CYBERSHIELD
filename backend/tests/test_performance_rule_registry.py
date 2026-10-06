"""Performance regression test (Phase 7, Part 9) for the rule
enable/disable gate (rule_registry_service.py). Each `quick_classify` call
(one per link, capped at 20 per email) queries DetectionRule once — no
caching (see rule_registry_service.py's docstring for why a flask.g-based
cache turned out to be unsafe here). This test's job is to catch a
regression that makes that per-link cost worse than O(1) queries per link,
and to confirm the feature stays correct at that scale.
"""

from sqlalchemy import event

from app.extensions import db
from tests.conftest import csrf_header


def _login(client, registered_user):
    client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )


def _count_detection_rule_queries(app, fn):
    counter = {"n": 0}

    def _on_execute(conn, cursor, statement, parameters, context, executemany):
        if "detection_rules" in statement:
            counter["n"] += 1

    with app.app_context():
        event.listen(db.engine, "before_cursor_execute", _on_execute)
        try:
            result = fn()
        finally:
            event.remove(db.engine, "before_cursor_execute", _on_execute)
    return counter["n"], result


def test_email_scan_query_count_scales_linearly_not_worse_with_link_count(app, client, registered_user):
    _login(client, registered_user)

    def scan_with_n_links(n):
        body = "From: a@example.com\nSubject: Hi\n\n" + "".join(f"https://example.com/page-{i}\n" for i in range(n))
        return client.post("/api/v1/email/scan", data={"email_text": body}, headers=csrf_header(client))

    few_queries, few_response = _count_detection_rule_queries(app, lambda: scan_with_n_links(1))
    many_queries, many_response = _count_detection_rule_queries(app, lambda: scan_with_n_links(15))

    assert few_response.status_code == 201
    assert many_response.status_code == 201

    # One query per link (url category) plus one for the email category
    # rules themselves — not quadratic, not unbounded.
    assert few_queries <= 2
    assert many_queries <= 16


def test_disabling_a_rule_takes_effect_immediately_on_the_very_next_scan(client, admin_user):
    client.post(
        "/api/v1/auth/login", json={"email": admin_user["email"], "password": admin_user["password"]}
    )
    rules = client.get("/api/v1/admin/rules?category=url").get_json()["items"]
    https_rule = next(r for r in rules if r["key"].endswith("https_check"))

    client.put(f"/api/v1/admin/rules/{https_rule['id']}", json={"enabled": False}, headers=csrf_header(client))

    result = client.post(
        "/api/v1/url/scan", json={"url": "http://example.com"}, headers=csrf_header(client)
    ).get_json()
    assert not any(r["rule"] == "https_check" for r in result["rules"])
