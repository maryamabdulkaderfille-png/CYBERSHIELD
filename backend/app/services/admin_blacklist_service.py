"""Admin Blacklist Management (Phase 7). CRUD over the existing
BlacklistEntry table the url_scanner's blacklist_check rule already reads
from — no new detection logic, just an admin-facing wrapper."""

from app.extensions import db
from app.models.blacklist import BlacklistEntry
from app.services.url_scanner.domain_utils import registrable_domain
from app.utils.errors import APIError


def list_entries(page: int, per_page: int, search: str | None = None, enabled: bool | None = None):
    query = BlacklistEntry.query
    if search:
        query = query.filter(BlacklistEntry.domain.ilike(f"%{search}%"))
    if enabled is not None:
        query = query.filter_by(enabled=enabled)

    query = query.order_by(BlacklistEntry.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total


def add_entry(domain: str, reason: str, added_by_user_id: str) -> BlacklistEntry:
    normalized = registrable_domain(domain.strip().lower())
    existing = BlacklistEntry.query.filter_by(domain=normalized).first()
    if existing is not None:
        raise APIError(f"'{normalized}' is already on the blacklist.", 409)

    entry = BlacklistEntry(domain=normalized, reason=reason.strip(), added_by_user_id=added_by_user_id)
    db.session.add(entry)
    db.session.commit()
    return entry


def get_entry_or_404(entry_id: int) -> BlacklistEntry:
    entry = db.session.get(BlacklistEntry, entry_id)
    if entry is None:
        raise APIError("Blacklist entry not found.", 404)
    return entry


def remove_entry(entry_id: int) -> None:
    entry = get_entry_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()


def set_enabled(entry_id: int, enabled: bool) -> BlacklistEntry:
    entry = get_entry_or_404(entry_id)
    entry.enabled = enabled
    db.session.commit()
    return entry
