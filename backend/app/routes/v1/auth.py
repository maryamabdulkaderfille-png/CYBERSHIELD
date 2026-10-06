from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, jsonify, redirect, request, url_for
from flask_jwt_extended import (
    create_access_token,
    decode_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
)
from marshmallow import ValidationError

from app.extensions import db, limiter, oauth
from app.models.audit_log import AuditAction, AuditStatus
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordSchema,
    LoginSchema,
    RegisterSchema,
    ResendVerificationSchema,
    ResetPasswordSchema,
    VerifyEmailSchema,
)
from app.services import audit_service, auth_service, session_service
from app.utils.errors import APIError

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
@limiter.limit("5 per minute")
def register():
    try:
        data = RegisterSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    user = auth_service.register_user(
        full_name=data["full_name"],
        username=data["username"],
        email=data["email"],
        password=data["password"],
    )

    response = jsonify(
        {"message": "Account created. Check your email to verify your account.", "user": user.to_public_dict()}
    )
    response.status_code = 201
    access_token, refresh_token, session_key = auth_service.issue_token_pair(user)
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    session_service.record_session(
        user.id, refresh_token, session_key, request.headers.get("User-Agent"), request.remote_addr
    )
    return response


@auth_bp.post("/login")
@limiter.limit("10 per minute")
def login():
    try:
        data = LoginSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    try:
        user = auth_service.authenticate_user(data["email"], data["password"])
    except APIError:
        audit_service.log_action(
            None, AuditAction.LOGIN, request.remote_addr, AuditStatus.FAILURE, email=data["email"]
        )
        raise

    response = jsonify({"message": "Login successful.", "user": user.to_public_dict()})
    access_token, refresh_token, session_key = auth_service.issue_token_pair(user)
    set_access_cookies(response, access_token)

    if data.get("remember_me"):
        remember_max_age = int(timedelta(days=30).total_seconds())
        set_refresh_cookies(response, refresh_token, max_age=remember_max_age)
    else:
        set_refresh_cookies(response, refresh_token)

    session_service.record_session(
        user.id, refresh_token, session_key, request.headers.get("User-Agent"), request.remote_addr
    )
    audit_service.log_action(user.id, AuditAction.LOGIN, request.remote_addr, AuditStatus.SUCCESS)
    return response


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    user = db.session.get(User, identity)
    if user is None or not user.is_active:
        return jsonify({"error": "Account not found or deactivated."}), 401

    claims = get_jwt()
    access_token = create_access_token(
        identity=identity, additional_claims={"role": claims.get("role"), "sid": claims.get("sid")}
    )
    response = jsonify({"message": "Token refreshed."})
    set_access_cookies(response, access_token)
    session_service.touch_session(claims["jti"])
    return response


@auth_bp.post("/logout")
@jwt_required(optional=True)
def logout():
    claims = get_jwt()
    if claims:
        auth_service.revoke_token(
            jti=claims["jti"],
            token_type=claims.get("type", "access"),
            user_id=claims.get("sub"),
            expires_at=datetime.fromtimestamp(claims["exp"], tz=timezone.utc).replace(tzinfo=None),
        )

    refresh_cookie = request.cookies.get(current_app.config["JWT_REFRESH_COOKIE_NAME"])
    if refresh_cookie:
        try:
            refresh_claims = decode_token(refresh_cookie)
        except Exception:
            refresh_claims = None
        if refresh_claims:
            auth_service.revoke_token(
                jti=refresh_claims["jti"],
                token_type=refresh_claims.get("type", "refresh"),
                user_id=refresh_claims.get("sub"),
                expires_at=datetime.fromtimestamp(refresh_claims["exp"], tz=timezone.utc).replace(
                    tzinfo=None
                ),
            )
            session_service.mark_session_revoked_by_jti(refresh_claims["jti"])

    if claims:
        audit_service.log_action(claims.get("sub"), AuditAction.LOGOUT, request.remote_addr, AuditStatus.SUCCESS)

    response = jsonify({"message": "Logged out."})
    unset_jwt_cookies(response)
    return response


@auth_bp.post("/forgot-password")
@limiter.limit("5 per minute")
def forgot_password():
    try:
        data = ForgotPasswordSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    auth_service.request_password_reset(data["email"])
    audit_service.log_action(
        None, AuditAction.PASSWORD_RESET_REQUESTED, request.remote_addr, email=data["email"]
    )
    return jsonify({"message": "If that email exists, a reset link has been sent."})


@auth_bp.post("/reset-password")
@limiter.limit("5 per minute")
def reset_password():
    try:
        data = ResetPasswordSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    user = auth_service.reset_password(data["token"], data["password"])
    audit_service.log_action(user.id, AuditAction.PASSWORD_RESET_COMPLETED, request.remote_addr)
    return jsonify({"message": "Password has been reset. You can now log in."})


@auth_bp.post("/verify-email")
def verify_email():
    try:
        data = VerifyEmailSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    user = auth_service.verify_email(data["token"])
    return jsonify({"message": "Email verified.", "user": user.to_public_dict()})


@auth_bp.post("/resend-verification")
@limiter.limit("3 per minute")
def resend_verification():
    try:
        data = ResendVerificationSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed.", "details": err.messages}), 422

    auth_service.resend_verification_email(data["email"])
    return jsonify({"message": "If that account needs verification, an email has been sent."})


# --- Google Sign-In (Phase 11) -----------------------------------------
#
# Additive alternative to the email/password flow above — every route
# above this comment is completely unmodified. Both routes here are real
# browser navigations (the frontend uses window.location.href, never the
# axios API client), since the OAuth redirect dance has to happen in the
# browser itself, not an XHR/fetch call.


@auth_bp.get("/google/login")
@limiter.limit("10 per minute")
def google_login():
    if not hasattr(oauth, "google"):
        raise APIError("Google Sign-In is not configured on this server.", 501)
    # auth_bp is nested inside api_v1_bp (see routes/v1/__init__.py), so the
    # endpoint's full dotted name includes that parent blueprint's name too.
    redirect_uri = url_for("api_v1.auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.get("/google/callback")
def google_callback():
    if not hasattr(oauth, "google"):
        raise APIError("Google Sign-In is not configured on this server.", 501)

    frontend_login = f"{current_app.config['FRONTEND_BASE_URL']}/login"
    try:
        # Authlib validates the id_token's signature (against Google's real
        # JWKS), issuer, audience, nonce, and expiry internally as part of
        # this call — the resulting claims land in token["userinfo"], not
        # something this route trusts blindly from the response body.
        token = oauth.google.authorize_access_token()
        claims = token.get("userinfo")
    except Exception:
        current_app.logger.warning("Google OAuth callback failed to authorize/verify token.")
        return redirect(f"{frontend_login}?error=google_failed")

    if not claims or not claims.get("email") or not claims.get("email_verified"):
        return redirect(f"{frontend_login}?error=google_unverified_email")

    user = auth_service.find_or_create_google_user(
        google_id=claims["sub"], email=claims["email"], full_name=claims.get("name", "")
    )
    if not user.is_active:
        return redirect(f"{frontend_login}?error=account_deactivated")

    response = redirect(f"{current_app.config['FRONTEND_BASE_URL']}/dashboard")
    access_token, refresh_token, session_key = auth_service.issue_token_pair(user)
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    session_service.record_session(
        user.id, refresh_token, session_key, request.headers.get("User-Agent"), request.remote_addr
    )
    audit_service.log_action(user.id, AuditAction.LOGIN, request.remote_addr, AuditStatus.SUCCESS, method="google")
    return response
