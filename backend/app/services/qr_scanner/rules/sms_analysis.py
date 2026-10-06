"""QR codes containing an `sms:`/`smsto:` message are checked for phishing
language ("smishing") by reusing the Phase 3 Email Scanner's urgency and
threat-language rules directly on the message body — the same social-
engineering phrase lists apply regardless of channel, so nothing is
duplicated here.
"""

import dataclasses

from app.constants import RiskLevel
from app.services.email_scanner.rules import threat_language, urgency_detection
from app.services.email_scanner.types import EmailContext
from app.services.qr_scanner.types import RuleResult, Severity


def analyze(parsed_fields: dict):
    message = parsed_fields.get("message") or ""
    number = parsed_fields.get("number") or "unknown"

    if not message:
        rule_results = [
            RuleResult(
                rule="sms_content",
                label="SMS Content",
                triggered=False,
                impact=0,
                severity=Severity.INFO,
                message=f"No message body found in this SMS QR code (destination: {number}).",
            )
        ]
        return 90, "Safe", [], ["Verify the recipient number before sending any SMS."], rule_results

    ctx = EmailContext(
        sender_display_name=None,
        sender_email=None,
        subject=None,
        body_text=message,
        body_html=None,
    )
    findings = [urgency_detection.evaluate(ctx), threat_language.evaluate(ctx)]

    rule_results = [RuleResult(**dataclasses.asdict(f)) for f in findings]
    score = 100 + sum(r.impact for r in rule_results)
    score = max(0, min(100, score))
    risk = RiskLevel.from_score(score)
    reasons = [f"✔ {f.message}" for f in findings if f.triggered]
    recommendations = ["Do not reply to or act on suspicious SMS messages from unfamiliar numbers."]
    if any(f.triggered for f in findings):
        recommendations.insert(0, "This message uses language commonly seen in SMS phishing (\"smishing\") scams.")

    return score, risk, reasons, recommendations, rule_results
