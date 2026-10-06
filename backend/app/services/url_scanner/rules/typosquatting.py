"""Flags domains that closely resemble a well-known brand domain.

Two independent checks, both scored as the same "typosquatting" rule:

1. The registrable domain itself is within a small Levenshtein edit
   distance of a known brand domain — catching classic typosquats like
   `paypaI.com`, `arnazon.com`, or `goggle-login.net`.
2. A known brand name appears as its own label (or hyphen/underscore
   component of a label) somewhere in the *subdomain* portion of the
   hostname, while the actual registrable domain is unrelated — catching
   the "brand buried in a fake subdomain" trick, e.g.
   `accounts.google.com.freehost42.ru` or `secure-paypal.example.net`,
   where a glance at the URL shows the brand name but the browser
   actually connects to the attacker's domain.

Both are static, offline heuristics. A production system would extend
this with a live brand-monitoring feed; the `KNOWN_BRAND_DOMAINS` list
below is the integration point for that.
"""

import re

from app.services.url_scanner.domain_utils import registrable_domain
from app.services.url_scanner.rules.suspicious_keywords import KEYWORDS as _LURE_KEYWORDS
from app.services.url_scanner.types import RuleResult, ScanContext, Severity

KNOWN_BRAND_DOMAINS = [
    "google.com",
    "paypal.com",
    "amazon.com",
    "microsoft.com",
    "apple.com",
    "facebook.com",
    "instagram.com",
    "netflix.com",
    "bankofamerica.com",
    "chase.com",
    "wellsfargo.com",
    "twitter.com",
    "linkedin.com",
    "dropbox.com",
    "adobe.com",
    "ebay.com",
    "outlook.com",
    "yahoo.com",
    "github.com",
    "steamcommunity.com",
]

# Brand name (no TLD) -> full brand domain, for the subdomain-impersonation
# check below.
_BRAND_TOKENS = {brand.split(".")[0]: brand for brand in KNOWN_BRAND_DOMAINS}

# Brand names that double as ordinary English words. Flagging these the
# instant they appear as a subdomain label would catch too many unrelated
# sites ("apple-pie-recipes.cookingblog.com", "chase-waterfalls.example.com",
# "amazon-rainforest-tours.example.com"), so for these specifically we also
# require a phishing-lure word nearby before treating the token as
# impersonation.
_AMBIGUOUS_BRAND_TOKENS = {"apple", "chase", "amazon"}

# Not a full public-suffix list — just the handful of two-part ccTLDs common
# enough that a real brand-owned country domain (e.g. "amazon.co.uk") would
# otherwise be misread by the naive last-two-labels split as "amazon" hiding
# in a subdomain of someone else's "co.uk".
_MULTI_PART_TLD_SUFFIXES = {
    "co.uk", "co.jp", "co.in", "co.nz", "co.za", "co.id",
    "com.au", "com.br", "com.mx", "com.sg",
}


def _subdomain_labels(hostname: str) -> list[str]:
    """The labels that come before the registrable domain, adjusting for
    `_MULTI_PART_TLD_SUFFIXES` so e.g. 'www.amazon.co.uk' treats 'amazon.co.uk'
    as the registrable domain rather than just 'co.uk'."""
    labels = [label for label in hostname.split(".") if label]
    if len(labels) >= 3 and ".".join(labels[-2:]) in _MULTI_PART_TLD_SUFFIXES:
        return labels[:-3]
    return labels[:-2]


def _subdomain_impersonation(hostname: str, reg_domain: str) -> RuleResult | None:
    """Flags a known brand name embedded as a subdomain label while the
    real registrable domain is unrelated to that brand."""
    labels = _subdomain_labels(hostname)
    if not labels:
        return None

    tokens = [t for label in labels for t in re.split(r"[-_]", label) if t]
    joined = "-".join(tokens)
    lure_present = any(
        re.search(rf"(?:^|[-_]){re.escape(kw)}(?:$|[-_])", joined) for kw in _LURE_KEYWORDS
    )

    for token in tokens:
        brand_domain = _BRAND_TOKENS.get(token)
        if not brand_domain:
            continue
        if token in _AMBIGUOUS_BRAND_TOKENS and not lure_present:
            continue
        return RuleResult(
            rule="typosquatting",
            label="Typosquatting",
            triggered=True,
            impact=-30,
            severity=Severity.CRITICAL,
            message=(
                f"Hostname contains '{token}' as a subdomain label, impersonating "
                f"{brand_domain}, while the real domain is '{reg_domain}'."
            ),
            detail=brand_domain,
        )
    return None


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    previous_row = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current_row = [i]
        for j, char_b in enumerate(b, start=1):
            cost = 0 if char_a == char_b else 1
            current_row.append(
                min(
                    previous_row[j] + 1,  # deletion
                    current_row[j - 1] + 1,  # insertion
                    previous_row[j - 1] + cost,  # substitution
                )
            )
        previous_row = current_row
    return previous_row[-1]


def evaluate(ctx: ScanContext) -> RuleResult:
    if ctx.is_ip_host or not ctx.hostname:
        return RuleResult(
            rule="typosquatting",
            label="Typosquatting",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="Not applicable.",
        )

    hostname = ctx.hostname.lower()
    domain = registrable_domain(hostname)

    for brand in KNOWN_BRAND_DOMAINS:
        if domain == brand:
            return RuleResult(
                rule="typosquatting",
                label="Typosquatting",
                triggered=False,
                impact=0,
                severity=Severity.INFO,
                message=f"Matches the legitimate domain for {brand}.",
            )

        distance = _levenshtein(domain, brand)
        length_ratio = abs(len(domain) - len(brand))
        if distance <= 2 and length_ratio <= 2:
            return RuleResult(
                rule="typosquatting",
                label="Typosquatting",
                triggered=True,
                impact=-30,
                severity=Severity.CRITICAL,
                message=f"Domain closely resembles well-known brand '{brand}' — likely typosquatting.",
                detail=brand,
            )

    impersonation = _subdomain_impersonation(hostname, domain)
    if impersonation:
        return impersonation

    return RuleResult(
        rule="typosquatting",
        label="Typosquatting",
        triggered=False,
        impact=0,
        severity=Severity.INFO,
        message="No resemblance to known brand domains detected.",
    )
