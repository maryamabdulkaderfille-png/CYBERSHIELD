"""Flags common phishing-lure keywords in the URL.

These words show up disproportionately in credential-harvesting and
prize/reward-scam URLs ("verify-account", "claim-your-bonus", etc.).
"""

import re

from app.services.url_scanner.types import RuleResult, ScanContext, Severity
from app.services.url_scanner.whitelist import is_whitelisted_domain

KEYWORDS = [
    "login",
    "verify",
    "update",
    "confirm",
    "secure",
    "bank",
    "wallet",
    "paypal",
    "password",
    "signin",
    "account",
    "authentication",
    "bonus",
    "gift",
    "prize",
    "reward",
    "reset",
]

IMPACT_PER_MATCH = -6
MAX_IMPACT = -24


def evaluate(ctx: ScanContext) -> RuleResult:
    if ctx.hostname:
        is_whitelisted, brand_name = is_whitelisted_domain(ctx.hostname)
        if is_whitelisted:
            return RuleResult(
                rule="suspicious_keywords",
                label="Suspicious Keywords",
                triggered=False,
                impact=0,
                severity=Severity.INFO,
                message=f"Keywords appear on official verified domain for {brand_name}.",
            )

    haystack = ctx.raw_url.lower()
    matched = [kw for kw in KEYWORDS if re.search(rf"[/.\-_?=]{re.escape(kw)}|^{re.escape(kw)}", haystack)]

    if not matched:
        return RuleResult(
            rule="suspicious_keywords",
            label="Suspicious Keywords",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="No suspicious keywords detected in the URL.",
        )

    impact = max(IMPACT_PER_MATCH * len(matched), MAX_IMPACT)
    return RuleResult(
        rule="suspicious_keywords",
        label="Suspicious Keywords",
        triggered=True,
        impact=impact,
        severity=Severity.MEDIUM if len(matched) > 1 else Severity.LOW,
        message=f"Contains suspicious keyword(s): {', '.join(matched)}.",
        detail=",".join(matched),
    )
