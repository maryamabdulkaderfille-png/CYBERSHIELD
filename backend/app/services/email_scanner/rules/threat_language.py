"""Flags threat/consequence language in the email body — phishing emails
manufacture a negative consequence (suspension, loss of access, financial
loss) to pressure the reader into clicking without verifying."""

from app.services.email_scanner.types import EmailContext, RuleResult, Severity

THREAT_PHRASES = [
    "account suspension",
    "account suspended",
    "payment failure",
    "payment failed",
    "security breach",
    "verify your identity",
    "login required",
    "update your information",
    "unauthorized access",
    "unusual activity",
]

IMPACT_PER_MATCH = -6
MAX_IMPACT = -20


def evaluate(ctx: EmailContext) -> RuleResult:
    body_lower = (ctx.body_text or "").lower()
    matched = [phrase for phrase in THREAT_PHRASES if phrase in body_lower]

    if not matched:
        return RuleResult(
            rule="threat_language",
            label="Threat Language",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="No threat/consequence language detected.",
        )

    impact = max(IMPACT_PER_MATCH * len(matched), MAX_IMPACT)
    return RuleResult(
        rule="threat_language",
        label="Threat Language",
        triggered=True,
        impact=impact,
        severity=Severity.MEDIUM if len(matched) > 1 else Severity.LOW,
        message=f"Uses threat/consequence language: {', '.join(matched)}.",
        detail=",".join(matched),
    )
