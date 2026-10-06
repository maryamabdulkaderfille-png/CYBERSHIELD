"""Basic format and premium-rate-pattern checks for `tel:` QR codes."""

import re

from app.services.qr_scanner.types import RuleResult, Severity

_VALID_PHONE_RE = re.compile(r"^\+?[0-9()\-.\s]{5,20}$")
_DIGITS_ONLY_RE = re.compile(r"\d")

# Well-known premium-rate / high-toll prefixes (not exhaustive — these are
# the most commonly abused in phishing/smishing campaigns).
_PREMIUM_PATTERNS = [
    re.compile(r"^\+?1?900"),  # NANP 1-900 premium numbers
    re.compile(r"^\+44\s?9"),  # UK 09 premium range
    re.compile(r"^\+61\s?190"),  # Australia 190x premium range
]


def analyze(parsed_fields: dict):
    number = (parsed_fields.get("number") or "").strip()

    if not number or not _VALID_PHONE_RE.match(number):
        reasons = ["✔ This QR code contains a malformed or invalid phone number."]
        rule_results = [
            RuleResult(
                rule="phone_format",
                label="Phone Format",
                triggered=True,
                impact=-30,
                severity=Severity.MEDIUM,
                message="Phone number is malformed or not in a recognizable format.",
            )
        ]
        return 40, "Suspicious", reasons, ["Verify this number independently before calling it."], rule_results

    digits = "".join(_DIGITS_ONLY_RE.findall(number))
    is_premium = any(pattern.match(number.replace(" ", "")) for pattern in _PREMIUM_PATTERNS)

    if is_premium:
        rule_results = [
            RuleResult(
                rule="phone_premium_rate",
                label="Premium-Rate Pattern",
                triggered=True,
                impact=-40,
                severity=Severity.HIGH,
                message="This number matches a known premium-rate pattern — calling it may incur high charges.",
            )
        ]
        return (
            30,
            "Dangerous",
            ["✔ This number matches a known premium-rate calling pattern."],
            ["Do not call this number.", "Premium-rate scams often arrive via QR code to bypass spam filters."],
            rule_results,
        )

    if len(digits) < 7:
        rule_results = [
            RuleResult(
                rule="phone_length",
                label="Phone Length",
                triggered=True,
                impact=-15,
                severity=Severity.LOW,
                message="Phone number is unusually short.",
            )
        ]
        return 70, "Low Risk", ["✔ Phone number is unusually short."], ["Verify this number before calling."], rule_results

    rule_results = [
        RuleResult(
            rule="phone_format",
            label="Phone Format",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="Phone number is validly formatted with no suspicious patterns.",
        )
    ]
    return 90, "Safe", [], ["Always verify unfamiliar phone numbers before calling."], rule_results
