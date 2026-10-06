"""Flags structural problems with the sender address itself:
missing sender, malformed address, or a free consumer email address whose
display name claims to represent an organization (e.g.
"PayPal Support" <support@gmail.com>).

Display-name impersonation of a *specific known brand* is handled separately
by display_name_impersonation.py, which owns the brand registry.
"""

import re

from app.services.email_scanner.brands import FREE_EMAIL_DOMAINS, ORGANIZATION_WORDS, domain_of
from app.services.email_scanner.types import EmailContext, RuleResult, Severity

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def evaluate(ctx: EmailContext) -> RuleResult:
    if not ctx.sender_email:
        return RuleResult(
            rule="sender_analysis",
            label="Sender Analysis",
            triggered=True,
            impact=-20,
            severity=Severity.HIGH,
            message="No sender address could be found on this email.",
        )

    if not _EMAIL_RE.match(ctx.sender_email):
        return RuleResult(
            rule="sender_analysis",
            label="Sender Analysis",
            triggered=True,
            impact=-15,
            severity=Severity.MEDIUM,
            message=f"Sender address '{ctx.sender_email}' is not a validly formatted email address.",
        )

    if ctx.sender_display_name and domain_of(ctx.sender_email) in FREE_EMAIL_DOMAINS:
        display_lower = ctx.sender_display_name.lower()
        if any(word in display_lower for word in ORGANIZATION_WORDS):
            return RuleResult(
                rule="sender_analysis",
                label="Sender Analysis",
                triggered=True,
                impact=-20,
                severity=Severity.HIGH,
                message=(
                    f"Display name '{ctx.sender_display_name}' suggests an organization, but the email "
                    f"comes from a free consumer email domain ({domain_of(ctx.sender_email)})."
                ),
            )

    return RuleResult(
        rule="sender_analysis",
        label="Sender Analysis",
        triggered=False,
        impact=0,
        severity=Severity.INFO,
        message="Sender address looks structurally normal.",
    )
