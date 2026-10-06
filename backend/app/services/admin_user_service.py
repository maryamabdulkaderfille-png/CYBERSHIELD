"""Admin User Management (Phase 7). Reuses the exact same services the
user's own profile/settings/session pages already use — this module never
recomputes stats or session state itself, it only calls those services with
an admin-supplied target user id instead of "the current user"."""

from app.extensions import db
from app.models.user import User, UserStatus
from app.services import session_service, unified_scan_service, user_profile_service
from app.utils.errors import APIError


def list_users(
    page: int,
    per_page: int,
    search: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    status: str | None = None,
) -> tuple[list[User], int]:
    query = User.query

    if search:
        like = f"%{search}%"
        query = query.filter(
            (User.username.ilike(like)) | (User.email.ilike(like)) | (User.full_name.ilike(like))
        )
    if role:
        query = query.filter_by(role=role)
    if is_active is not None:
        query = query.filter_by(is_active=is_active)
    if status:
        query = query.filter_by(status=status)
    else:
        # Removed accounts are soft-deleted, not hard-deleted (their scans/
        # audit rows must stay intact) — but they shouldn't clutter the
        # default admin user list. Pass status=removed explicitly to see them.
        query = query.filter(User.status != UserStatus.REMOVED)

    query = query.order_by(User.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total


def get_user_or_404(user_id: str) -> User:
    user = db.session.get(User, user_id)
    if user is None:
        raise APIError("User not found.", 404)
    return user


def get_user_detail(user_id: str) -> dict:
    user = get_user_or_404(user_id)
    return {
        "user": user.to_public_dict(),
        "stats": user_profile_service.get_profile_stats(user.id),
        "sessions": [s.to_dict() for s in session_service.list_sessions(user.id)],
    }


def get_user_recent_activity(user_id: str, limit: int = 20) -> list[dict]:
    get_user_or_404(user_id)
    items, _ = unified_scan_service.get_unified_scans(
        user_id, page=1, per_page=limit, filters=unified_scan_service.UnifiedScanFilters()
    )
    return items


def _revoke_all_sessions(user_id: str) -> None:
    """Immediately ends every session for this user — matches the guarantee
    level auth_service.deactivate_account (self-deactivation) already gives
    for a user's *other* sessions: refresh tokens are revoked right away, so
    /auth/refresh and new logins are blocked immediately. Same residual
    caveat self-deactivation already has: an already-issued access token
    for this user keeps working until its own short (15 min) expiry, since
    nothing in this codebase persists a lookup from user -> currently-live
    access-token jti to blocklist directly."""
    session_service.revoke_all_other_sessions(user_id, current_session_key=None)


def set_user_status(target_user_id: str, new_status: str) -> User:
    if new_status not in UserStatus.ALL:
        raise APIError(f"Unknown status: {new_status}", 422)

    user = get_user_or_404(target_user_id)
    user.status = new_status
    user.is_active = new_status == UserStatus.ACTIVE
    db.session.commit()

    if new_status != UserStatus.ACTIVE:
        _revoke_all_sessions(user.id)

    return user


def deactivate_user(target_user_id: str) -> User:
    """Kept for the existing POST /deactivate route — now also suspends via
    set_user_status so it gets the status field + session revocation this
    route was missing before, without changing its external behavior."""
    return set_user_status(target_user_id, UserStatus.SUSPENDED)


def reactivate_user(target_user_id: str) -> User:
    return set_user_status(target_user_id, UserStatus.ACTIVE)


def remove_user(target_user_id: str) -> User:
    return set_user_status(target_user_id, UserStatus.REMOVED)
