from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC now, matching how DateTime columns round-trip on both SQLite and Postgres."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
