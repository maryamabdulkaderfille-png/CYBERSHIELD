"""Classifies every link found in the email by reusing the Phase 2 URL
Scanner's detection rules — no URL-analysis logic is duplicated here.

Uses `quick_classify` (CPU-only rules: keywords, IP-host, typosquatting,
special characters, subdomains, blacklist — no live network calls) rather
than the full `scan_url`, since an email can contain many links and a full
scan of each would mean a TLS handshake + RDAP lookup + redirect-follow per
link, multiplying one email scan into dozens of outbound network calls.
"""

from app.services.email_scanner.types import EmailContext, LinkFinding, RuleResult, Severity
from app.services.url_scanner.engine import quick_classify
from app.services.url_scanner.types import RiskLevel

MAX_LINKS_TO_CLASSIFY = 20


def classify_links(links: list[str]) -> list[LinkFinding]:
    findings = []
    for url in links[:MAX_LINKS_TO_CLASSIFY]:
        score, risk = quick_classify(url)
        findings.append(LinkFinding(url=url, trust_score=score, risk=risk))
    return findings


def evaluate(ctx: EmailContext, findings: list[LinkFinding] | None = None) -> RuleResult:
    """`findings` lets the engine pass in an already-computed classification
    (it needs the same data for the detailed report) instead of classifying
    every link twice. Falls back to computing them when called standalone
    (e.g. in tests)."""
    if not ctx.links:
        return RuleResult(
            rule="link_analysis",
            label="Link Analysis",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="No links found in this email.",
        )

    if findings is None:
        findings = classify_links(ctx.links)

    dangerous = [f for f in findings if f.risk == RiskLevel.DANGEROUS]
    suspicious = [f for f in findings if f.risk == RiskLevel.SUSPICIOUS]

    if dangerous:
        return RuleResult(
            rule="link_analysis",
            label="Link Analysis",
            triggered=True,
            impact=-35,
            severity=Severity.CRITICAL,
            message=f"{len(dangerous)} of {len(findings)} link(s) found are classified as Dangerous.",
            detail=str(len(dangerous)),
        )

    if suspicious:
        return RuleResult(
            rule="link_analysis",
            label="Link Analysis",
            triggered=True,
            impact=-18,
            severity=Severity.MEDIUM,
            message=f"{len(suspicious)} of {len(findings)} link(s) found are classified as Suspicious.",
            detail=str(len(suspicious)),
        )

    return RuleResult(
        rule="link_analysis",
        label="Link Analysis",
        triggered=False,
        impact=0,
        severity=Severity.INFO,
        message=f"{len(findings)} link(s) found, all classified as Safe or Low Risk.",
    )
