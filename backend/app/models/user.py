import uuid

from app.extensions import db
from app.utils.time import utcnow


def _uuid() -> str:
    return str(uuid.uuid4())


def _isoformat_utc(value) -> str | None:
    return f"{value.isoformat()}Z" if value else None


class UserRole:
    USER = "user"
    ADMIN = "admin"
    ALL = (USER, ADMIN)


class UserStatus:
    """Richer, admin-facing label layered on top of the existing `is_active`
    flag — `is_active` stays the single enforcement gate everywhere it's
    already checked (login, /auth/refresh); `status` only distinguishes
    *why* an inactive account is inactive. Kept in sync by
    admin_user_service, never set directly: ACTIVE => is_active=True,
    SUSPENDED/REMOVED => is_active=False. REMOVED is a soft-delete (the row,
    and every FK reference to it in scans/audit_logs/blacklist_entries,
    stays intact) — it's excluded from the default admin user list rather
    than being a third enforcement state.
    """

    ACTIVE = "active"
    SUSPENDED = "suspended"
    REMOVED = "removed"
    ALL = (ACTIVE, SUSPENDED, REMOVED)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    # Nullable (Phase 11): an account created via "Sign in with Google" and
    # never linked to a password has no hash to store. Every account created
    # through the existing /auth/register flow still always gets one.
    password_hash = db.Column(db.String(255), nullable=True)
    # "Sign in with Google" (Phase 11) — Google's stable per-account
    # identifier ("sub" claim). Nullable/unique: NULL for every account that
    # has never linked Google, unique once set so one Google identity can
    # only ever map to one CyberShield account.
    google_id = db.Column(db.String(64), unique=True, nullable=True, index=True)
    role = db.Column(db.String(16), nullable=False, default=UserRole.USER)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    status = db.Column(db.String(16), nullable=False, default=UserStatus.ACTIVE)
    created_at = db.Column(db.DateTime(), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(), nullable=False, default=utcnow, onupdate=utcnow)
    last_login = db.Column(db.DateTime(), nullable=True)

    # Account lockout (Phase 10): tracked per-account in addition to the
    # existing IP-keyed rate limiting on /auth/login, so a distributed
    # credential-stuffing attempt against one account can't just spread
    # requests across IPs to dodge the rate limit.
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime(), nullable=True)

    # Extended profile fields (Phase 5) — all optional, additive.
    phone = db.Column(db.String(32), nullable=True)
    country = db.Column(db.String(2), nullable=True)  # ISO 3166-1 alpha-2
    bio = db.Column(db.String(500), nullable=True)
    avatar_url = db.Column(db.String(1024), nullable=True)

    tokens = db.relationship(
        "UserToken", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "is_verified": self.is_verified,
            "is_active": self.is_active,
            "status": self.status,
            "created_at": _isoformat_utc(self.created_at),
            "last_login": _isoformat_utc(self.last_login),
            "phone": self.phone,
            "country": self.country,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
        }

    def __repr__(self) -> str:
        return f"<User {self.username}>"
