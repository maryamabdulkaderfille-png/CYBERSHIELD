"""Admin-facing rule on/off switch (Phase 7) — shared by both scanner
engines so the "is this rule enabled" check is written once, not copied.

Never touches rule *logic*: it only decides whether a rule module's
existing, unmodified `evaluate()` gets called for a given scan. A missing
`DetectionRule` row is treated as enabled — this is what keeps every rule
running by default on a database that hasn't been seeded/migrated yet
(e.g. a test DB built via `db.create_all()`, which doesn't run data
migrations), so this table's mere existence can never accidentally disable
detection.

Deliberately queries fresh every call, with no request-scoped cache:
`flask.g` is bound to the *application context*, not the request, and an app
context can span multiple logical requests (this project's own test fixtures
push one app context around many `client.*()` calls) — a `g`-based cache
here would silently serve a stale enabled/disabled state across what look
like separate requests. A correctness bug is worse than the handful of
extra indexed SELECTs this costs (bounded at ~20/email scan, the link cap
already in place for other reasons) — see Part 9's "avoid premature
optimization" guidance.
"""

from app.models.detection_rule import DetectionRule


def _disabled_rule_names(category: str) -> set[str]:
    rows = DetectionRule.query.filter_by(category=category).all()
    return {row.key.rsplit(".", 1)[-1] for row in rows if not row.enabled}


def filter_enabled_rules(category: str, rules: list, rule_name) -> list:
    """`rule_name` is a function mapping a rule module to its bare name
    (e.g. "https_check"), matching how each engine already derives it."""
    disabled_names = _disabled_rule_names(category)
    if not disabled_names:
        return rules
    return [rule for rule in rules if rule_name(rule) not in disabled_names]


def rule_key(category: str, name: str) -> str:
    return f"{category}.{name}"
