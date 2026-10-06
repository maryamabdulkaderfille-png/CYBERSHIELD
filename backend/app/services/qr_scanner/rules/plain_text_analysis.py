"""Plain text QR content is displayed safely (escaped, never rendered as
HTML or executed) with no further phishing analysis — there's no
sender/link/attachment structure to evaluate."""

from app.services.qr_scanner.types import RuleResult, Severity


def analyze(parsed_fields: dict):
    rule_results = [
        RuleResult(
            rule="plain_text",
            label="Plain Text",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="This QR code contains plain text with no structured content to analyze.",
        )
    ]
    return (
        100,
        "Safe",
        [],
        ["Plain text QR codes carry no inherent risk, but stay cautious of any instructions it contains."],
        rule_results,
    )
