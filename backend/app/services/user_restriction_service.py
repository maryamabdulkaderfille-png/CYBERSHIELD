"""Per-user feature restrictions (admin-managed). Separate from `rbac.py`
on purpose: rbac is about what a *role* can do to the platform (admin
tooling); this is about which of a normal user's own features an admin has
switched off for them — a feature flag per account, not a permission tier.
"""

from functools import wraps

from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models.user_restriction import RestrictableFeature, UserRestriction
from app.utils.errors import APIError


def list_restrictions(user_id: str) -> list[UserRestriction]:
    return UserRestriction.query.filter_by(user_id=user_id).order_by(UserRestriction.restricted_at.desc()).all()


def is_restricted(user_id: str, feature: str) -> bool:
    return UserRestriction.query.filter_by(user_id=user_id, feature=feature).first() is not None


def add_restriction(user_id: str, feature: str, restricted_by_user_id: str) -> UserRestriction:
    if feature not in RestrictableFeature.ALL:
        raise APIError(f"Unknown feature: {feature}", 422)

    existing = UserRestriction.query.filter_by(user_id=user_id, feature=feature).first()
    if existing is not None:
        return existing  # Idempotent: adding an already-restricted feature is a no-op, not a 409.

    restriction = UserRestriction(user_id=user_id, feature=feature, restricted_by_user_id=restricted_by_user_id)
    db.session.add(restriction)
    db.session.commit()
    return restriction


def remove_restriction(user_id: str, feature: str) -> bool:
    restriction = UserRestriction.query.filter_by(user_id=user_id, feature=feature).first()
    if restriction is None:
        return False
    db.session.delete(restriction)
    db.session.commit()
    return True


def require_not_restricted(feature: str):
    """Server-side enforcement for a restricted feature — mirrors rbac's
    require_permission in shape (self-contained, includes @jwt_required())
    so a route only needs this one decorator. Checked on every request
    (restrictions can be lifted at any time), not cached in the JWT."""

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            if is_restricted(get_jwt_identity(), feature):
                raise APIError(
                    "Your account's access to this feature has been restricted by an administrator.", 403
                )
            return fn(*args, **kwargs)

        return wrapper

    return decorator
