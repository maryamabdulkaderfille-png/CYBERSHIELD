"""Flags punctuation tricks commonly used to obscure the real destination:

- `@` in the authority section (browsers ignore everything before it, so
  `http://google.com@evil.com` actually goes to evil.com) — escalated further
  when the fake portion before `@` looks like a spoofed domain or brand
  (`http://login.verify-paypal.com@evil.ru`), since that's a stronger signal
  of deliberate deception than the punctuation alone
- excessive `%` URL-encoding, often used to obfuscate a malicious path
- repeated `-`/`_` runs in the hostname, common in lookalike domains
- a second `//` appearing after the scheme, used to smuggle a second URL
"""

import re

from app.services.url_scanner.rules.suspicious_keywords import KEYWORDS as _LURE_KEYWORDS
from app.services.url_scanner.rules.typosquatting import KNOWN_BRAND_DOMAINS
from app.services.url_scanner.types import RuleResult, ScanContext, Severity

_BRAND_NAMES = [brand.split(".")[0] for brand in KNOWN_BRAND_DOMAINS]


def evaluate(ctx: ScanContext) -> RuleResult:
    findings: list[str] = []
    impact = 0
    severity = Severity.INFO

    if "@" in ctx.parsed.netloc:
        userinfo = (ctx.parsed.username or "").lower()
        looks_like_domain = "." in userinfo
        impersonates_brand = any(brand in userinfo for brand in _BRAND_NAMES)
        has_lure_keyword = any(kw in userinfo for kw in _LURE_KEYWORDS)

        if looks_like_domain and (impersonates_brand or has_lure_keyword):
            findings.append(
                f"host section is preceded by a fake domain-like string '{ctx.parsed.username}' "
                "impersonating the real destination — classic '@' phishing trick"
            )
            impact -= 35
            severity = Severity.CRITICAL
        else:
            findings.append("contains '@' in the host section")
            impact -= 20
            severity = Severity.HIGH

    percent_count = ctx.raw_url.count("%")
    if percent_count >= 3:
        findings.append(f"excessive URL-encoding ({percent_count} '%' characters)")
        impact -= 10
        severity = max(severity, Severity.MEDIUM, key=_severity_rank)

    if re.search(r"-{2,}", ctx.hostname) or ctx.hostname.count("-") >= 4:
        findings.append("repeated or excessive hyphens in the domain")
        impact -= 8
        severity = max(severity, Severity.LOW, key=_severity_rank)

    if re.search(r"_{2,}", ctx.hostname) or ctx.hostname.count("_") >= 3:
        findings.append("repeated or excessive underscores in the domain")
        impact -= 8
        severity = max(severity, Severity.LOW, key=_severity_rank)

    after_scheme = ctx.raw_url.split("://", 1)[-1]
    if "//" in after_scheme:
        findings.append("contains a second '//' after the domain, which can smuggle a hidden redirect")
        impact -= 10
        severity = max(severity, Severity.MEDIUM, key=_severity_rank)

    if not findings:
        return RuleResult(
            rule="special_characters",
            label="Special Characters",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="No suspicious punctuation patterns detected.",
        )

    return RuleResult(
        rule="special_characters",
        label="Special Characters",
        triggered=True,
        impact=impact,
        severity=severity,
        message="Suspicious punctuation: " + "; ".join(findings) + ".",
    )


_SEVERITY_ORDER = [Severity.INFO, Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]


def _severity_rank(value: str) -> int:
    return _SEVERITY_ORDER.index(value)
