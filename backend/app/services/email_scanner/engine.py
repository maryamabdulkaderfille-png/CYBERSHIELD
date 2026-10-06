from datetime import datetime, timezone

from app.services.email_scanner.rules import RULES, attachment_analysis, link_analysis
from app.services.email_scanner.rules.attachment_analysis import classify_attachment
from app.services.email_scanner.rules.link_analysis import classify_links
from app.services.email_scanner.types import EmailContext, EmailReport, RiskLevel, RuleResult
from app.services.rule_registry_service import filter_enabled_rules


def _rule_name(rule_module) -> str:
    return rule_module.__name__.rsplit(".", 1)[-1]

MAX_SCORE = 100
MIN_SCORE = 0

RECOMMENDATION_BY_RULE = {
    "sender_analysis": "Verify the sender's address independently before trusting this email.",
    "display_name_impersonation": "Do not trust the display name — check the actual sender domain, or contact the organization directly using a known official channel.",
    "urgency_detection": "Be skeptical of any email pressuring you to act immediately.",
    "threat_language": "Do not act on threats of suspension or loss of access without verifying through the official website or app.",
    "link_analysis": "Do not click the links in this email. Navigate to the official website directly instead.",
    "attachment_analysis": "Do not open the attachment(s) in this email.",
    "html_analysis": "Do not enter any information into forms embedded in this email.",
}

BASE_RISK_RECOMMENDATIONS = [
    "Do not reply to this email or provide any personal information.",
    "Verify the sender through a separate, trusted channel before taking any action.",
    "Delete the email if you cannot verify its legitimacy.",
]


def _build_reasons(rule_results: list[RuleResult]) -> list[str]:
    return [f"✔ {r.message}" for r in rule_results if r.triggered]


def _build_recommendations(rule_results: list[RuleResult], risk_level: str) -> list[str]:
    recommendations: list[str] = []

    if risk_level in {RiskLevel.SUSPICIOUS, RiskLevel.DANGEROUS}:
        recommendations.extend(BASE_RISK_RECOMMENDATIONS)

    for result in rule_results:
        if result.triggered and result.rule in RECOMMENDATION_BY_RULE:
            recommendation = RECOMMENDATION_BY_RULE[result.rule]
            if recommendation not in recommendations:
                recommendations.append(recommendation)

    if not recommendations:
        recommendations.append(
            "No significant risk indicators were found. Always stay cautious with unexpected emails."
        )

    return recommendations


def analyze_email(ctx: EmailContext) -> EmailReport:
    # Computed once up front: both the link/attachment rules and the
    # detailed report need this same classification data, and each
    # classification (network-free, but not free) shouldn't be done twice.
    link_findings = classify_links(ctx.links)
    attachment_findings = [classify_attachment(a.filename) for a in ctx.attachments]

    active_rules = filter_enabled_rules("email", RULES, _rule_name)

    rule_results = []
    for rule in active_rules:
        if rule is link_analysis:
            rule_results.append(rule.evaluate(ctx, link_findings))
        elif rule is attachment_analysis:
            rule_results.append(rule.evaluate(ctx, attachment_findings))
        else:
            rule_results.append(rule.evaluate(ctx))

    score = MAX_SCORE + sum(r.impact for r in rule_results)
    score = max(MIN_SCORE, min(MAX_SCORE, score))
    risk_level = RiskLevel.from_score(score)

    return EmailReport(
        trust_score=score,
        risk_level=risk_level,
        reasons=_build_reasons(rule_results),
        recommendations=_build_recommendations(rule_results, risk_level),
        rule_results=rule_results,
        links=link_findings,
        attachments=attachment_findings,
        sender_display_name=ctx.sender_display_name,
        sender_email=ctx.sender_email,
        subject=ctx.subject,
        scanned_at=datetime.now(timezone.utc),
    )
