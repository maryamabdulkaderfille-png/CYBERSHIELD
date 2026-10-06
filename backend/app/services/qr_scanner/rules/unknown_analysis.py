"""Content that couldn't be decoded or classified is treated cautiously by
default — displayed safely (never executed/rendered as HTML), with a
suspicious-by-default posture since it can't be positively identified as
safe.
"""

from app.services.qr_scanner.types import RuleResult, Severity


def analyze(parsed_fields: dict):
    rule_results = [
        RuleResult(
            rule="unknown_content",
            label="Unknown Content",
            triggered=True,
            impact=-30,
            severity=Severity.MEDIUM,
            message="This QR code's content could not be classified into a known, safe category.",
        )
    ]
    return (
        60,
        "Suspicious",
        ["✔ This QR code's content could not be classified into a known, safe category."],
        ["Treat unrecognized QR content with caution.", "Do not manually type or act on this content unless you trust its source."],
        rule_results,
    )
