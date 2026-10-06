from datetime import timedelta

from app.constants import RiskLevel
from app.extensions import db
from app.models.notification import Notification, NotificationType
from app.models.scan import ScanHistory
from app.models.user import User, UserStatus
from app.models.user_settings import UserSettings
from app.services import weekly_summary_service
from app.utils.time import utcnow


def _add_scan(user_id, risk_level, days_ago=0):
    scan = ScanHistory(
        user_id=user_id,
        url="https://example.com",
        trust_score=50,
        risk_level=risk_level,
        scan_result={},
        analysis_details={"rules": []},
        scan_date=utcnow() - timedelta(days=days_ago),
    )
    db.session.add(scan)
    db.session.commit()
    return scan


def test_no_users_creates_nothing(app):
    with app.app_context():
        assert weekly_summary_service.generate_weekly_summaries() == 0


def test_user_with_no_settings_row_is_eligible_by_default(app, registered_user_id):
    with app.app_context():
        _add_scan(registered_user_id, RiskLevel.DANGEROUS)
        created = weekly_summary_service.generate_weekly_summaries()
        assert created == 1
        notif = Notification.query.filter_by(user_id=registered_user_id).one()
        assert notif.type == NotificationType.WEEKLY_SUMMARY
        assert "1 scan" in notif.message
        assert "1 flagged Dangerous" in notif.message


def test_toggle_off_skips_user(app, registered_user_id):
    with app.app_context():
        db.session.add(UserSettings(user_id=registered_user_id, notify_weekly_summary=False))
        db.session.commit()
        assert weekly_summary_service.generate_weekly_summaries() == 0


def test_suspended_user_is_skipped(app, registered_user_id):
    with app.app_context():
        user = db.session.get(User, registered_user_id)
        user.status = UserStatus.SUSPENDED
        db.session.commit()
        assert weekly_summary_service.generate_weekly_summaries() == 0


def test_scans_outside_window_not_counted(app, registered_user_id):
    with app.app_context():
        _add_scan(registered_user_id, RiskLevel.SAFE, days_ago=1)
        _add_scan(registered_user_id, RiskLevel.DANGEROUS, days_ago=10)

        weekly_summary_service.generate_weekly_summaries()
        notif = Notification.query.filter_by(user_id=registered_user_id).one()
        assert "1 scan" in notif.message
        assert "0 flagged Dangerous" in notif.message


def test_does_not_duplicate_within_gap_window(app, registered_user_id):
    with app.app_context():
        _add_scan(registered_user_id, RiskLevel.SAFE)
        assert weekly_summary_service.generate_weekly_summaries() == 1
        assert weekly_summary_service.generate_weekly_summaries() == 0
        assert Notification.query.filter_by(user_id=registered_user_id).count() == 1


def test_multiple_eligible_users_each_get_one(app, registered_user_id, second_user_id):
    with app.app_context():
        _add_scan(registered_user_id, RiskLevel.SAFE)
        _add_scan(second_user_id, RiskLevel.SUSPICIOUS)

        created = weekly_summary_service.generate_weekly_summaries()
        assert created == 2
        assert Notification.query.filter_by(user_id=registered_user_id).count() == 1
        assert Notification.query.filter_by(user_id=second_user_id).count() == 1
