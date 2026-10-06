from app.models.user import User
from app.models.user_token import TokenPurpose
from app.services import token_service


def test_full_password_reset_flow(app, client, registered_user):
    with app.app_context():
        user = User.query.filter_by(email=registered_user["email"]).first()
        raw_token = token_service.issue_token(user.id, TokenPurpose.PASSWORD_RESET)

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": raw_token,
            "password": "NewStrongPass1!",
            "confirm_password": "NewStrongPass1!",
        },
    )
    assert response.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": "NewStrongPass1!"},
    )
    assert login.status_code == 200

    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    assert old_login.status_code == 401


def test_reset_token_cannot_be_reused(app, client, registered_user):
    with app.app_context():
        user = User.query.filter_by(email=registered_user["email"]).first()
        raw_token = token_service.issue_token(user.id, TokenPurpose.PASSWORD_RESET)

    first = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "password": "NewStrongPass1!", "confirm_password": "NewStrongPass1!"},
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "password": "AnotherPass1!", "confirm_password": "AnotherPass1!"},
    )
    assert second.status_code == 400


def test_verify_email_flow(app, client, registered_user):
    with app.app_context():
        user = User.query.filter_by(email=registered_user["email"]).first()
        assert user.is_verified is False
        raw_token = token_service.issue_token(user.id, TokenPurpose.EMAIL_VERIFICATION)

    response = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert response.status_code == 200
    assert response.get_json()["user"]["is_verified"] is True
