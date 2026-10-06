from urllib.parse import urlparse

import pytest

from app.services import block_list_service, community_intel_service, explanation_service
from app.utils.errors import APIError


# --- block_list_service: never-block guard (Feature 10) --------------------


def test_assert_blockable_rejects_localhost():
    with pytest.raises(APIError):
        block_list_service.assert_blockable("localhost")


def test_assert_blockable_rejects_loopback_ip():
    with pytest.raises(APIError):
        block_list_service.assert_blockable("127.0.0.1")


@pytest.mark.parametrize("ip", ["192.168.1.1", "10.0.0.5", "172.16.0.1", "169.254.1.1"])
def test_assert_blockable_rejects_private_ip_ranges(app, ip):
    with app.app_context(), pytest.raises(APIError):
        block_list_service.assert_blockable(ip)


def test_assert_blockable_rejects_frontend_origin(app):
    with app.app_context():
        frontend_host = urlparse(app.config["FRONTEND_ORIGIN"]).hostname
        with pytest.raises(APIError):
            block_list_service.assert_blockable(frontend_host)


def test_assert_blockable_allows_a_public_domain(app):
    with app.app_context():
        block_list_service.assert_blockable("evil-phish.example")  # must not raise


def test_assert_blockable_allows_a_public_ip(app):
    with app.app_context():
        block_list_service.assert_blockable("8.8.8.8")  # must not raise


def test_extract_hostname_normalizes_full_url_to_registrable_domain():
    assert block_list_service.extract_hostname("https://www.evil-phish.example/login?x=1") == "evil-phish.example"


def test_extract_hostname_accepts_bare_domain():
    assert block_list_service.extract_hostname("Evil-Phish.Example") == "evil-phish.example"


# --- block_list_service: block/unblock/restore lifecycle --------------------


def test_block_website_creates_entry(app, registered_user_id):
    with app.app_context():
        entry = block_list_service.block_website(
            registered_user_id, "https://evil.example/login", 8, "Dangerous", ["Newly registered domain"]
        )
        assert entry.domain == "evil.example"
        assert entry.is_active is True
        assert entry.trust_score == 8


def test_block_website_rejects_duplicate_active_entry(app, registered_user_id):
    with app.app_context():
        block_list_service.block_website(registered_user_id, "evil.example", 8, "Dangerous", [])
        with pytest.raises(APIError):
            block_list_service.block_website(registered_user_id, "evil.example", 8, "Dangerous", [])


def test_unblock_then_reblock_reactivates_same_row(app, registered_user_id):
    with app.app_context():
        first = block_list_service.block_website(registered_user_id, "evil.example", 8, "Dangerous", [])
        block_list_service.unblock(registered_user_id, first.id)
        second = block_list_service.block_website(registered_user_id, "evil.example", 5, "Dangerous", ["updated reason"])
        assert second.id == first.id
        assert second.is_active is True
        assert second.trust_score == 5


def test_unblock_is_always_allowed(app, registered_user_id):
    with app.app_context():
        entry = block_list_service.block_website(registered_user_id, "evil.example", 8, "Dangerous", [])
        unblocked = block_list_service.unblock(registered_user_id, entry.id)
        assert unblocked.is_active is False
        assert unblocked.unblocked_at is not None


def test_restore_reactivates_a_removed_entry(app, registered_user_id):
    with app.app_context():
        entry = block_list_service.block_website(registered_user_id, "evil.example", 8, "Dangerous", [])
        block_list_service.unblock(registered_user_id, entry.id)
        restored = block_list_service.restore(registered_user_id, entry.id)
        assert restored.is_active is True
        assert restored.unblocked_at is None


def test_list_blocked_filters_by_active_state(app, registered_user_id):
    with app.app_context():
        active = block_list_service.block_website(registered_user_id, "active.example", 8, "Dangerous", [])
        removed = block_list_service.block_website(registered_user_id, "removed.example", 8, "Dangerous", [])
        block_list_service.unblock(registered_user_id, removed.id)

        active_items, active_total = block_list_service.list_blocked(registered_user_id, 1, 20, is_active=True)
        removed_items, removed_total = block_list_service.list_blocked(registered_user_id, 1, 20, is_active=False)

        assert active_total == 1 and active_items[0].id == active.id
        assert removed_total == 1 and removed_items[0].id == removed.id


def test_get_active_entries_lite_only_returns_active(app, registered_user_id):
    with app.app_context():
        entry = block_list_service.block_website(registered_user_id, "active.example", 8, "Dangerous", ["reason one"])
        removed = block_list_service.block_website(registered_user_id, "removed.example", 8, "Dangerous", [])
        block_list_service.unblock(registered_user_id, removed.id)

        lite = block_list_service.get_active_entries_lite(registered_user_id)
        domains = {row["domain"] for row in lite}
        assert domains == {"active.example"}
        assert lite[0]["reason"] == "reason one"


def test_export_json_and_csv_include_inactive_entries(app, registered_user_id):
    with app.app_context():
        entry = block_list_service.block_website(registered_user_id, "evil.example", 8, "Dangerous", [])
        block_list_service.unblock(registered_user_id, entry.id)

        json_export = block_list_service.export_json(registered_user_id)
        csv_export = block_list_service.export_csv(registered_user_id)

        assert len(json_export) == 1
        assert "evil.example" in csv_export


# --- community_intel_service -------------------------------------------------


def test_get_community_intel_counts_distinct_users(app, registered_user_id, second_user_id):
    with app.app_context():
        block_list_service.block_website(registered_user_id, "shared-threat.example", 8, "Dangerous", [])
        block_list_service.block_website(second_user_id, "shared-threat.example", 5, "Dangerous", [])

        intel = community_intel_service.get_community_intel(["shared-threat.example"])
        assert intel["shared-threat.example"]["blocked_by_users"] == 2
        assert intel["shared-threat.example"]["confidence_percent"] == 40


def test_get_community_intel_empty_for_unknown_domain(app):
    with app.app_context():
        assert community_intel_service.get_community_intel(["never-blocked.example"]) == {}


def test_maybe_alert_user_is_deduplicated(app, registered_user_id, second_user_id):
    with app.app_context():
        from app.models.notification import Notification, NotificationType

        # Three OTHER users block the domain to cross the alert threshold.
        for i in range(3):
            other_user_id = _make_extra_user(app, f"other{i}@example.com")
            block_list_service.block_website(other_user_id, "hot-threat.example", 5, "Dangerous", [])

        community_intel_service.maybe_alert_user(registered_user_id, "hot-threat.example")
        community_intel_service.maybe_alert_user(registered_user_id, "hot-threat.example")

        alerts = Notification.query.filter_by(
            user_id=registered_user_id, type=NotificationType.COMMUNITY_THREAT_ALERT
        ).all()
        assert len(alerts) == 1


def _make_extra_user(app, email):
    from app.services import auth_service

    user = auth_service.register_user("Extra User", email.split("@")[0], email, "StrongPass1!")
    return user.id


# --- explanation_service (Feature 7 — not real AI, purely templated) --------


def test_generate_explanation_uses_triggered_rules_sorted_by_severity():
    rules = [
        {"triggered": True, "severity": "low", "message": "low sev message"},
        {"triggered": True, "severity": "critical", "message": "critical sev message"},
        {"triggered": False, "severity": "high", "message": "not triggered, excluded"},
    ]
    result = explanation_service.generate_explanation("Dangerous", 5, ["fallback reason"], rules)
    assert result["points"][0] == "critical sev message"
    assert "not triggered, excluded" not in result["points"]


def test_generate_explanation_falls_back_to_reasons_when_no_rules_triggered():
    result = explanation_service.generate_explanation("Dangerous", 5, ["only a reason"], [])
    assert result["points"] == ["only a reason"]


@pytest.mark.parametrize(
    "risk,expected_snippet",
    [
        ("Dangerous", "Do not enter"),
        ("Suspicious", "Proceed carefully"),
        ("Safe", "No significant"),
    ],
)
def test_generate_explanation_risk_specific_summary(risk, expected_snippet):
    result = explanation_service.generate_explanation(risk, 50, [], [])
    assert expected_snippet in result["summary"] or expected_snippet in result["recommendation"]
