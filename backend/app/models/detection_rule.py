from app.extensions import db
from app.utils.time import utcnow


class RuleCategory:
    URL = "url"
    EMAIL = "email"
    ALL = (URL, EMAIL)


class DetectionRule(db.Model):
    """Admin-facing metadata + on/off switch for a detection rule module
    (Phase 7). This table never contains detection *logic* — it only gates
    whether `url_scanner.engine`/`email_scanner.engine` calls a given rule
    module's existing `evaluate()` function for a scan (see engine.py's
    `_is_rule_enabled` — a missing row is treated as enabled, so an
    un-seeded table never silently disables every rule).
    """

    __tablename__ = "detection_rules"

    id = db.Column(db.Integer, primary_key=True)
    # "<category>.<rule module name>", e.g. "url.https_check" — matches the
    # RuleResult.rule string plus its scanner, so it's unambiguous across
    # the two scanners' rule namespaces.
    key = db.Column(db.String(64), nullable=False, unique=True, index=True)
    category = db.Column(db.String(16), nullable=False)
    label = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    severity = db.Column(db.String(16), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    # Bumped every time an admin toggles `enabled` — a simple, honest stand-in
    # for "rule version" until rule *content* (not just on/off) is editable.
    version = db.Column(db.Integer, nullable=False, default=1)
    updated_at = db.Column(db.DateTime(), nullable=False, default=utcnow, onupdate=utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "category": self.category,
            "label": self.label,
            "description": self.description,
            "severity": self.severity,
            "enabled": self.enabled,
            "version": self.version,
            "updated_at": f"{self.updated_at.isoformat()}Z",
        }
