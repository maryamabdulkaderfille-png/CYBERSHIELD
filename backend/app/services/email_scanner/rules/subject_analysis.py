"""Flags common phishing-lure phrases in the subject line."""

from app.services.email_scanner.types import EmailContext, RuleResult, Severity

SUBJECT_KEYWORDS = [
    "urgent",
    "verify",
    "confirm",
    "suspended",
    "payment failed",
    "your account",
    "security alert",
    "password reset",
    "lottery",
    "prize",
    "gift",
    "reward",
    "limited time",
    "immediate action required",
]

IMPACT_PER_MATCH = -6
MAX_IMPACT = -24


def evaluate(ctx: EmailContext) -> RuleResult:
    if not ctx.subject:
        return RuleResult(
            rule="subject_analysis",
            label="Subject Analysis",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="No subject to analyze.",
        )

    subject_lower = ctx.subject.lower()
    matched = [kw for kw in SUBJECT_KEYWORDS if kw in subject_lower]

    if not matched:
        return RuleResult(
            rule="subject_analysis",
            label="Subject Analysis",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="Subject line does not contain common phishing lures.",
        )

    impact = max(IMPACT_PER_MATCH * len(matched), MAX_IMPACT)
    return RuleResult(
        rule="subject_analysis",
        label="Subject Analysis",
        triggered=True,
        impact=impact,
        severity=Severity.MEDIUM if len(matched) > 1 else Severity.LOW,
        message=f"Subject contains phishing-lure phrase(s): {', '.join(matched)}.",
        detail=",".join(matched),
    )
