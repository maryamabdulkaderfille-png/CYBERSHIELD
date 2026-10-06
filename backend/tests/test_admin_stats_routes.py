def _login(client, user):
    client.post("/api/v1/auth/login", json={"email": user["email"], "password": user["password"]})


def test_stats_requires_admin(client, registered_user):
    _login(client, registered_user)
    assert client.get("/api/v1/admin/stats").status_code == 403


def test_stats_requires_auth(client):
    assert client.get("/api/v1/admin/stats").status_code == 401


def test_stats_shape(client, admin_user):
    _login(client, admin_user)
    response = client.get("/api/v1/admin/stats")
    assert response.status_code == 200
    body = response.get_json()

    assert "overview" in body and "threat_intelligence" in body
    for key in ("users", "scans", "extension_activity", "notifications_sent", "recent_logins", "system_health"):
        assert key in body["overview"]
    for key in (
        "known_phishing_domains",
        "most_common_keywords",
        "detection_trends",
        "threat_statistics",
        "severity_distribution",
    ):
        assert key in body["threat_intelligence"]


def test_stats_composes_same_data_as_the_split_endpoints(client, admin_user):
    """/admin/stats must not diverge from what /admin/dashboard and /threats
    already report — it's a composition, not a second copy of the logic."""
    _login(client, admin_user)
    overview = client.get("/api/v1/admin/dashboard").get_json()
    threat_intel = client.get("/api/v1/threats").get_json()

    stats = client.get("/api/v1/admin/stats").get_json()
    assert stats["overview"]["users"] == overview["users"]
    assert stats["threat_intelligence"]["threat_statistics"] == threat_intel["threat_statistics"]


# --- Live active-user count ---------------------------------------------------


def test_active_users_shape(client, admin_user):
    _login(client, admin_user)
    body = client.get("/api/v1/admin/stats").get_json()
    assert "active_users" in body
    assert body["active_users"]["window_minutes"] == 15
    assert isinstance(body["active_users"]["count"], int)


def test_active_users_counts_distinct_logged_in_users(app, client, admin_user, registered_user):
    second_client = app.test_client()
    second_client.post(
        "/api/v1/auth/login", json={"email": registered_user["email"], "password": registered_user["password"]}
    )

    _login(client, admin_user)
    count = client.get("/api/v1/admin/stats").get_json()["active_users"]["count"]
    assert count >= 2  # the admin (via `client`) and registered_user (via `second_client`)


def test_active_users_excludes_sessions_older_than_the_window(app, client, admin_user, registered_user):
    from datetime import timedelta

    from app.extensions import db
    from app.models.user_session import UserSession
    from app.utils.time import utcnow

    second_client = app.test_client()
    second_client.post(
        "/api/v1/auth/login", json={"email": registered_user["email"], "password": registered_user["password"]}
    )

    _login(client, admin_user)
    count_before = client.get("/api/v1/admin/stats").get_json()["active_users"]["count"]

    with app.app_context():
        # Push every session's last_seen_at outside the 15-minute window.
        # Plain GET requests never touch last_seen_at (only /auth/refresh
        # does, via touch_session), so no session re-enters the window here.
        UserSession.query.update({UserSession.last_seen_at: utcnow() - timedelta(minutes=30)})
        db.session.commit()

    count_after = client.get("/api/v1/admin/stats").get_json()["active_users"]["count"]
    assert count_before >= 2
    assert count_after == 0
