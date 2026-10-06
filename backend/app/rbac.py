"""Role-based access control (Phase 7).

`User.role` (see app/models/user.py) can only ever be "user" or "admin"
today — nothing in this codebase accepts a client-supplied role, and the
registration flow always defaults to "user". This module defines the
*architecture* for a richer role set ahead of time (Security Analyst,
Viewer) so activating them later is a matter of allowing a new value in
`UserRole.ALL` and wiring up a way to assign it — no route, decorator, or
permission check anywhere needs to change. Every admin route below is
gated by `require_permission(...)`, never a hardcoded `role == "admin"`
string comparison, specifically so that future roles can be granted a
subset of admin permissions without touching route code.
"""

from functools import wraps

from flask_jwt_extended import get_jwt, jwt_required

from app.utils.errors import APIError


class Role:
    ADMIN = "admin"
    SECURITY_ANALYST = "security_analyst"
    USER = "user"
    VIEWER = "viewer"
    ALL = (ADMIN, SECURITY_ANALYST, USER, VIEWER)


# Every permission string used by an admin route today. Roles other than
# ADMIN are not yet assignable to a real account (see the module docstring)
# — their entries here are prepared, not exercised, until a future phase
# adds a way to actually grant those roles.
PERMISSIONS: dict[str, set[str]] = {
    Role.ADMIN: {
        "users.view",
        "users.manage",
        "scans.view",
        "scans.manage",
        "blacklist.manage",
        "rules.manage",
        "audit.view",
        "system.monitor",
    },
    Role.SECURITY_ANALYST: {"users.view", "scans.view", "blacklist.manage", "rules.manage", "audit.view"},
    Role.VIEWER: {"users.view", "scans.view", "audit.view"},
    Role.USER: set(),
}


def has_permission(role: str | None, permission: str) -> bool:
    return permission in PERMISSIONS.get(role or "", set())


def require_permission(permission: str):
    """Self-contained: already includes `@jwt_required()`, so a route only
    needs this one decorator. Reads the `role` claim already embedded in
    every access token (see auth_service.issue_token_pair) rather than
    re-querying the user."""

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            role = get_jwt().get("role")
            if not has_permission(role, permission):
                raise APIError("You do not have permission to perform this action.", 403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator
