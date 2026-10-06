from app.rbac import PERMISSIONS, Role, has_permission
from tests.conftest import csrf_header


def _login(client, user):
    client.post("/api/v1/auth/login", json={"email": user["email"], "password": user["password"]})


def test_has_permission_true_for_admin_permissions():
    assert has_permission(Role.ADMIN, "users.manage") is True
    assert has_permission(Role.ADMIN, "system.monitor") is True


def test_has_permission_false_for_plain_user():
    assert has_permission(Role.USER, "users.manage") is False
    assert has_permission(Role.USER, "audit.view") is False


def test_has_permission_false_for_unknown_role():
    assert has_permission("not-a-real-role", "users.manage") is False
    assert has_permission(None, "users.manage") is False


def test_future_roles_are_defined_but_not_assignable_today():
    # Architecture-readiness check (Part 2): the permission matrix already
    # has entries for roles no account can actually hold yet.
    assert Role.SECURITY_ANALYST in PERMISSIONS
    assert Role.VIEWER in PERMISSIONS
    assert PERMISSIONS[Role.SECURITY_ANALYST]
    assert PERMISSIONS[Role.VIEWER]


def test_admin_endpoint_rejects_plain_user(client, registered_user):
    _login(client, registered_user)
    response = client.get("/api/v1/admin/dashboard")
    assert response.status_code == 403


def test_admin_endpoint_rejects_unauthenticated(client):
    response = client.get("/api/v1/admin/dashboard")
    assert response.status_code == 401


def test_admin_endpoint_allows_admin(client, admin_user):
    _login(client, admin_user)
    response = client.get("/api/v1/admin/dashboard")
    assert response.status_code == 200


def test_admin_mutation_requires_csrf_like_any_other_route(client, admin_user):
    _login(client, admin_user)
    # No CSRF header attached — should be rejected the same way any other
    # mutating endpoint already is (no special-cased bypass for admin routes).
    response = client.post("/api/v1/admin/blacklist", json={"domain": "example-phish.test"})
    assert response.status_code in (400, 401, 403)


def test_admin_mutation_succeeds_with_csrf(client, admin_user):
    _login(client, admin_user)
    response = client.post(
        "/api/v1/admin/blacklist",
        json={"domain": "example-phish.test", "reason": "test"},
        headers=csrf_header(client),
    )
    assert response.status_code == 201
