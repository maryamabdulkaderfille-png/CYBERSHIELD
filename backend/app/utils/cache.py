"""Caching architecture placeholder (Phase 5).

`cacheable` is a no-op decorator: it documents *where* a cache should sit
(around expensive, platform-wide aggregation queries) without introducing a
real cache backend, which is explicitly out of scope for this phase. A real
implementation (e.g. Redis, with `ttl_seconds` actually enforced) can wrap
the same decorated functions later without changing any call sites.
"""

from functools import wraps


def cacheable(ttl_seconds: int):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.cache_ttl_seconds = ttl_seconds
        wrapper.is_cacheable_placeholder = True
        return wrapper

    return decorator
