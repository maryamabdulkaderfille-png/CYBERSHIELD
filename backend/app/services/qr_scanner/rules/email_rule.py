"""QR codes containing a `mailto:` target are analyzed with the full Phase 3
Email Scanner engine — no phishing-heuristic logic is duplicated here.

The mailto target address is treated as the email's `sender_email` for
analysis purposes: a QR code that makes you email
"support@paypal-verify.com" is functionally the same impersonation pattern
the sender-analysis and display-name-impersonation rules already catch. Any
fields the mailto URI doesn't provide (display name, body, links,
attachments) are simply absent from the context — every Phase 3 rule
already degrades gracefully (not triggered) when its input is missing, so
no extra "whenever applicable" branching is needed here.
"""

import dataclasses

from app.services.email_scanner.engine import analyze_email
from app.services.email_scanner.types import EmailContext
from app.services.qr_scanner.types import RuleResult


def analyze(parsed_fields: dict):
    ctx = EmailContext(
        sender_display_name=None,
        sender_email=parsed_fields.get("address") or None,
        subject=parsed_fields.get("subject") or None,
        body_text=parsed_fields.get("body") or "",
        body_html=None,
        links=[],
        attachments=[],
        headers={},
        parse_defects=[],
    )
    report = analyze_email(ctx)
    rule_results = [RuleResult(**dataclasses.asdict(r)) for r in report.rule_results]
    return report.trust_score, report.risk_level, report.reasons, report.recommendations, rule_results
