"""Flags social-engineering urgency language in the email body — pressuring
the reader to act before they think is one of the oldest phishing tricks."""

from app.services.email_scanner.types import EmailContext, RuleResult, Severity

URGENCY_PHRASES = [
    "immediately",
    "act now",
    "within 24 hours",
    "final warning",
    "last chance",
    "urgent response required",
    "act fast",
    "time sensitive",
    "expires soon",
    "right away",
]

IMPACT_PER_MATCH = -6
MAX_IMPACT = -20


def evaluate(ctx: EmailContext) -> RuleResult:
    body_lower = (ctx.body_text or "").lower()
    matched = [phrase for phrase in URGENCY_PHRASES if phrase in body_lower]

    if not matched:
        return RuleResult(
            rule="urgency_detection",
            label="Urgency Detection",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="No urgency-pressure language detected.",
        )

    impact = max(IMPACT_PER_MATCH * len(matched), MAX_IMPACT)
    return RuleResult(
        rule="urgency_detection",
        label="Urgency Detection",
        triggered=True,
        impact=impact,
        severity=Severity.MEDIUM if len(matched) > 1 else Severity.LOW,
        message=f"Uses urgency/pressure language: {', '.join(matched)}.",
        detail=",".join(matched),
    )
