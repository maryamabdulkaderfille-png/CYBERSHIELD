"""Crypto wallet QR codes get format validation and a standard security
warning only — no blockchain lookup or balance/transaction verification is
performed (out of scope, per the platform's design)."""

from app.constants import RiskLevel
from app.services.qr_scanner.types import RuleResult, Severity

STANDARD_RECOMMENDATIONS = [
    "Always verify the recipient address independently before sending funds.",
    "Cryptocurrency transactions cannot be reversed — double-check the address character by character.",
]


def analyze(parsed_fields: dict):
    network = parsed_fields.get("network", "Unknown network")
    is_valid = bool(parsed_fields.get("is_valid_format"))

    if not is_valid:
        rule_results = [
            RuleResult(
                rule="crypto_format",
                label="Wallet Format",
                triggered=True,
                impact=-50,
                severity=Severity.HIGH,
                message=f"Wallet address does not match a recognized format for {network}.",
            )
        ]
        return (
            30,
            "Dangerous",
            [f"✔ Wallet address does not match a recognized format for {network}."],
            ["Do not send funds to this address.", *STANDARD_RECOMMENDATIONS],
            rule_results,
        )

    rule_results = [
        RuleResult(
            rule="crypto_format",
            label="Wallet Format",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message=f"Wallet address matches a valid {network} format.",
        )
    ]
    return 85, RiskLevel.LOW_RISK, [], STANDARD_RECOMMENDATIONS, rule_results
