"""Admin Rule Management (Phase 7). Manages DetectionRule rows only — the
on/off switch and metadata for each rule module; never the rule logic
itself (see rule_registry_service.py for how the engines honor `enabled`,
and RULE_REGISTRY below for where each rule's metadata is defined once).
"""

from app.extensions import db
from app.models.detection_rule import DetectionRule, RuleCategory
from app.services.rule_registry_service import rule_key
from app.utils.errors import APIError

# Mined from each rule module's own RuleResult literals (see the url_scanner
# and email_scanner rules/ packages) — this is metadata *about* each rule,
# never a second copy of its logic. Severity here is each rule's own
# triggered-case severity.
RULE_REGISTRY: list[dict] = [
    # --- URL scanner rules ---
    {"name": "whitelist_check", "category": RuleCategory.URL, "label": "Verified Safe List", "severity": "info",
     "description": "Grants trust reinforcement for domains on CyberShield's curated high-reputation brand list."},
    {"name": "url_length", "category": RuleCategory.URL, "label": "URL Length", "severity": "medium",
     "description": "Flags unusually long or short URLs, a common phishing-link obfuscation signal."},
    {"name": "https_check", "category": RuleCategory.URL, "label": "HTTPS", "severity": "medium",
     "description": "Flags URLs that don't use HTTPS (unencrypted traffic)."},
    {"name": "ssl_certificate", "category": RuleCategory.URL, "label": "SSL Certificate", "severity": "high",
     "description": "Performs a real TLS handshake and flags invalid, expired, or unverifiable certificates."},
    {"name": "ip_address", "category": RuleCategory.URL, "label": "IP Address Host", "severity": "high",
     "description": "Flags URLs that use a raw IP address instead of a domain name."},
    {"name": "suspicious_keywords", "category": RuleCategory.URL, "label": "Suspicious Keywords", "severity": "medium",
     "description": "Flags login/verify/bank/wallet/paypal-style phishing lure keywords in the URL."},
    {"name": "special_characters", "category": RuleCategory.URL, "label": "Special Characters", "severity": "high",
     "description": "Flags '@' in the host, excessive '%' encoding, repeated '-'/'_', and smuggled '//'."},
    {"name": "subdomains", "category": RuleCategory.URL, "label": "Subdomains", "severity": "high",
     "description": "Flags unusually deep subdomain chains, a common brand-impersonation tactic."},
    {"name": "typosquatting", "category": RuleCategory.URL, "label": "Typosquatting", "severity": "critical",
     "description": "Flags domains within a small edit distance of a well-known brand domain."},
    {"name": "domain_age", "category": RuleCategory.URL, "label": "Domain Age", "severity": "medium",
     "description": "Looks up domain registration age via RDAP; recently-registered domains are riskier."},
    {"name": "blacklist_check", "category": RuleCategory.URL, "label": "Blacklist", "severity": "critical",
     "description": "Checks the domain against CyberShield's own blacklist table."},
    {"name": "redirect_check", "category": RuleCategory.URL, "label": "Redirect Chain", "severity": "medium",
     "description": "Follows redirects (SSRF-safe) and flags long chains or a cross-domain final destination."},
    {"name": "external_threat_intel", "category": RuleCategory.URL, "label": "Global Threat Intelligence", "severity": "critical",
     "description": "Checks the URL/domain against VirusTotal and URLhaus threat feeds for confirmed malicious activity."},
    # --- Email scanner rules ---
    {"name": "sender_analysis", "category": RuleCategory.EMAIL, "label": "Sender Analysis", "severity": "high",
     "description": "Flags missing/malformed sender addresses and free-provider addresses claiming to be an organization."},
    {"name": "display_name_impersonation", "category": RuleCategory.EMAIL, "label": "Display Name Impersonation", "severity": "critical",
     "description": "Flags a display name naming a specific known brand whose sender domain doesn't match."},
    {"name": "subject_analysis", "category": RuleCategory.EMAIL, "label": "Subject Analysis", "severity": "medium",
     "description": "Flags phishing-lure phrases in the subject line."},
    {"name": "greeting_analysis", "category": RuleCategory.EMAIL, "label": "Greeting Analysis", "severity": "low",
     "description": "Flags generic greetings ('Dear Customer') instead of a real name."},
    {"name": "urgency_detection", "category": RuleCategory.EMAIL, "label": "Urgency Detection", "severity": "medium",
     "description": "Flags pressure language ('act now', 'within 24 hours')."},
    {"name": "threat_language", "category": RuleCategory.EMAIL, "label": "Threat Language", "severity": "medium",
     "description": "Flags consequence language ('account suspension', 'security breach')."},
    {"name": "link_analysis", "category": RuleCategory.EMAIL, "label": "Link Analysis", "severity": "critical",
     "description": "Classifies every link in the email via the URL scanner's quick_classify."},
    {"name": "attachment_analysis", "category": RuleCategory.EMAIL, "label": "Attachment Analysis", "severity": "critical",
     "description": "Flags dangerous extensions and double-extension disguises."},
    {"name": "html_analysis", "category": RuleCategory.EMAIL, "label": "HTML Analysis", "severity": "critical",
     "description": "Flags embedded scripts/forms, hidden elements, and obfuscated encoding."},
    {"name": "grammar_heuristics", "category": RuleCategory.EMAIL, "label": "Grammar Heuristics", "severity": "info",
     "description": "Light-touch, low-weight signals (repeated punctuation, ALL-CAPS ratio) — deliberately capped."},
]


def ensure_seeded() -> None:
    """Lazily creates any RULE_REGISTRY rows missing from the table — safe
    to call every time (idempotent), so a fresh DB self-heals on first
    admin access without requiring the data migration to have run."""
    existing_keys = {row.key for row in DetectionRule.query.all()}
    for entry in RULE_REGISTRY:
        key = rule_key(entry["category"], entry["name"])
        if key in existing_keys:
            continue
        db.session.add(
            DetectionRule(
                key=key,
                category=entry["category"],
                label=entry["label"],
                description=entry["description"],
                severity=entry["severity"],
                enabled=True,
            )
        )
    db.session.commit()


def list_rules(category: str | None = None) -> list[DetectionRule]:
    ensure_seeded()
    query = DetectionRule.query
    if category:
        query = query.filter_by(category=category)
    return query.order_by(DetectionRule.category, DetectionRule.label).all()


def get_rule_or_404(rule_id: int) -> DetectionRule:
    rule = db.session.get(DetectionRule, rule_id)
    if rule is None:
        raise APIError("Detection rule not found.", 404)
    return rule


def set_enabled(rule_id: int, enabled: bool) -> DetectionRule:
    rule = get_rule_or_404(rule_id)
    if rule.enabled != enabled:
        rule.enabled = enabled
        rule.version += 1
        db.session.commit()
    return rule
