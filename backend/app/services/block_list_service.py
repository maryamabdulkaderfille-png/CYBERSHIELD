"""Personal Block List (Phase 9) — reuses the existing URL scanner's SSRF-safe
public-IP validator (app.services.url_scanner.network.is_public_ip) for the
"never block private/internal addresses" guard, and the same
registrable-domain heuristic (domain_utils.registrable_domain) the admin
Blacklist and typosquatting/domain-age rules already use — no duplicated
domain-parsing logic.

A block is created from an existing Dangerous scan result (manually via the
"Block Website" panel, or automatically by the browser extension under an
auto-block Active Protection mode) — this module never scores a URL itself.
"""

import csv
import io
from ipaddress import ip_address
from urllib.parse import urlparse

from flask import current_app

from app.extensions import db
from app.models.blocked_website import BlockedWebsite
from app.services.url_scanner.domain_utils import registrable_domain
from app.services.url_scanner.network import is_public_ip
from app.utils.errors import APIError
from app.utils.time import utcnow

_LOOPBACK_HOSTNAMES = {"localhost", "localhost.localdomain", "127.0.0.1", "::1"}

SORTABLE_FIELDS = {"blocked_at": BlockedWebsite.blocked_at, "domain": BlockedWebsite.domain, "trust_score": BlockedWebsite.trust_score}


def extract_hostname(target: str) -> str:
    """Accepts either a bare domain/IP or a full URL and returns a
    normalized hostname — a registrable domain ("evil.com") for real domain
    names (same shape `admin_blacklist_service` normalizes to), but a raw IP
    address is returned as-is: `registrable_domain`'s "last two labels"
    heuristic is for DNS names and would otherwise mangle an IP address
    (e.g. "192.168.1.1" -> "1.1"), silently defeating the private-IP guard
    in `assert_blockable` below."""
    value = target.strip().lower()
    if "://" in value:
        value = urlparse(value).hostname or value
    else:
        value = value.split("/")[0].split(":")[0]

    try:
        ip_address(value)
        return value
    except ValueError:
        return registrable_domain(value)


def assert_blockable(hostname: str) -> None:
    """Feature 10: never allow blocking localhost, private/internal IP
    ranges, or CyberShield's own frontend."""
    if hostname in _LOOPBACK_HOSTNAMES:
        raise APIError("CyberShield does not allow blocking localhost.", 422)

    frontend_host = urlparse(current_app.config["FRONTEND_ORIGIN"]).hostname
    if frontend_host and hostname == frontend_host:
        raise APIError("CyberShield does not allow blocking its own website.", 422)

    try:
        addr = ip_address(hostname)
    except ValueError:
        return  # a domain name, not a literal IP — nothing further to check
    if not is_public_ip(addr):
        raise APIError("CyberShield does not allow blocking private/internal IP addresses.", 422)


def list_blocked(
    user_id: str,
    page: int,
    per_page: int,
    search: str | None = None,
    risk_level: str | None = None,
    is_active: bool | None = True,
    sort_by: str = "blocked_at",
    sort_dir: str = "desc",
):
    query = BlockedWebsite.query.filter_by(user_id=user_id)
    if is_active is not None:
        query = query.filter_by(is_active=is_active)
    if search:
        query = query.filter(BlockedWebsite.domain.ilike(f"%{search}%"))
    if risk_level:
        query = query.filter_by(risk_level=risk_level)

    column = SORTABLE_FIELDS.get(sort_by, BlockedWebsite.blocked_at)
    query = query.order_by(column.asc() if sort_dir == "asc" else column.desc())

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total


def get_or_404(user_id: str, entry_id: int) -> BlockedWebsite:
    entry = BlockedWebsite.query.filter_by(id=entry_id, user_id=user_id).first()
    if entry is None:
        raise APIError("Blocked website not found.", 404)
    return entry


def block_website(
    user_id: str,
    target: str,
    trust_score: int,
    risk_level: str,
    reasons: list[str],
    scanner_type: str = "url",
    scan_id: int | None = None,
) -> BlockedWebsite:
    domain = extract_hostname(target)
    assert_blockable(domain)

    existing = BlockedWebsite.query.filter_by(user_id=user_id, domain=domain).first()
    if existing is not None:
        if existing.is_active:
            raise APIError(f"'{domain}' is already on your block list.", 409)
        # Re-blocking a previously-removed domain reactivates the same row
        # instead of violating the (user_id, domain) uniqueness constraint.
        existing.trust_score = trust_score
        existing.risk_level = risk_level
        existing.reasons = reasons
        existing.scanner_type = scanner_type
        existing.scan_id = scan_id
        existing.is_active = True
        existing.blocked_at = utcnow()
        existing.unblocked_at = None
        db.session.commit()
        return existing

    entry = BlockedWebsite(
        user_id=user_id,
        domain=domain,
        trust_score=trust_score,
        risk_level=risk_level,
        reasons=reasons,
        scanner_type=scanner_type,
        scan_id=scan_id,
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def unblock(user_id: str, entry_id: int) -> BlockedWebsite:
    """Feature 10: always allowed, regardless of protection mode."""
    entry = get_or_404(user_id, entry_id)
    entry.is_active = False
    entry.unblocked_at = utcnow()
    db.session.commit()
    return entry


def restore(user_id: str, entry_id: int) -> BlockedWebsite:
    entry = get_or_404(user_id, entry_id)
    entry.is_active = True
    entry.unblocked_at = None
    entry.blocked_at = utcnow()
    db.session.commit()
    return entry


def get_active_entries_lite(user_id: str) -> list[dict]:
    """Used by the browser extension sync endpoint — just enough per entry to
    both enforce the block AND render the "Access Blocked" warning page's
    trust score/reason (id, domain, trust_score, risk_level, one reason)
    without a second network round trip when a blocked page is opened."""
    rows = BlockedWebsite.query.filter_by(user_id=user_id, is_active=True).all()
    return [
        {
            "id": row.id,
            "domain": row.domain,
            "trust_score": row.trust_score,
            "risk_level": row.risk_level,
            "reason": (row.reasons or [None])[0],
            "scanner_type": row.scanner_type,
            "scan_id": row.scan_id,
        }
        for row in rows
    ]


def export_json(user_id: str) -> list[dict]:
    items, _ = list_blocked(user_id, page=1, per_page=10_000, is_active=None)
    return [item.to_dict() for item in items]


def export_csv(user_id: str) -> str:
    items, _ = list_blocked(user_id, page=1, per_page=10_000, is_active=None)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["domain", "trust_score", "risk_level", "reasons", "scanner_type", "scan_id", "is_active", "blocked_at", "unblocked_at"])
    for item in items:
        writer.writerow(
            [
                item.domain,
                item.trust_score,
                item.risk_level,
                "; ".join(item.reasons or []),
                item.scanner_type,
                item.scan_id or "",
                item.is_active,
                item.blocked_at.isoformat(),
                item.unblocked_at.isoformat() if item.unblocked_at else "",
            ]
        )
    return buffer.getvalue()
