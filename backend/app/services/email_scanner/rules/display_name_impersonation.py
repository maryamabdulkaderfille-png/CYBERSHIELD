"""Flags a display name that names a specific well-known brand while the
sender's actual domain isn't one of that brand's legitimate domains —
e.g. "Microsoft Account Team" <security@micros0ft-verify.com>.

Add new brands in `email_scanner.brands.KNOWN_BRANDS` — no changes needed
here.
"""

from app.services.email_scanner.brands import KNOWN_BRANDS, domain_of
from app.services.email_scanner.types import EmailContext, RuleResult, Severity


def evaluate(ctx: EmailContext) -> RuleResult:
    if not ctx.sender_display_name or not ctx.sender_email:
        return RuleResult(
            rule="display_name_impersonation",
            label="Display Name Impersonation",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="Not applicable.",
        )

    display_lower = ctx.sender_display_name.lower()
    sender_domain = domain_of(ctx.sender_email)

    for brand, legitimate_domains in KNOWN_BRANDS.items():
        if brand in display_lower and sender_domain not in legitimate_domains:
            return RuleResult(
                rule="display_name_impersonation",
                label="Display Name Impersonation",
                triggered=True,
                impact=-30,
                severity=Severity.CRITICAL,
                message=(
                    f"Display name references '{brand.title()}' but the sender domain "
                    f"({sender_domain}) is not an official {brand.title()} domain."
                ),
                detail=brand,
            )

    return RuleResult(
        rule="display_name_impersonation",
        label="Display Name Impersonation",
        triggered=False,
        impact=0,
        severity=Severity.INFO,
        message="Display name does not appear to impersonate a known brand.",
    )
