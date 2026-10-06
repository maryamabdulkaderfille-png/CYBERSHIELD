"""Flags generic, impersonal greetings — legitimate organizations that
already have your account details almost always address you by name."""

import re

from app.services.email_scanner.types import EmailContext, RuleResult, Severity

GENERIC_GREETINGS = [
    r"dear\s+customer",
    r"dear\s+user",
    r"dear\s+client",
    r"dear\s+member",
    r"dear\s+account\s+holder",
    r"dear\s+valued\s+customer",
    r"dear\s+sir\s*/?\s*madam",
]

_PATTERN = re.compile("|".join(GENERIC_GREETINGS), re.IGNORECASE)


def evaluate(ctx: EmailContext) -> RuleResult:
    match = _PATTERN.search(ctx.body_text or "")
    if not match:
        return RuleResult(
            rule="greeting_analysis",
            label="Greeting Analysis",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="No generic greeting detected.",
        )

    return RuleResult(
        rule="greeting_analysis",
        label="Greeting Analysis",
        triggered=True,
        impact=-8,
        severity=Severity.LOW,
        message=f"Uses a generic greeting ('{match.group(0).strip()}') instead of your name.",
    )
