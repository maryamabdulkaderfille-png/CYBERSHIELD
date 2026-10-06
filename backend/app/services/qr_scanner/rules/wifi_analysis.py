"""WiFi QR codes are informational — CyberShield can't verify whether a
network actually belongs to who the SSID claims, so this never exposes the
password and only offers general caution rather than a phishing verdict.
"""

from app.constants import RiskLevel
from app.services.qr_scanner.types import RuleResult, Severity


def analyze(parsed_fields: dict):
    ssid = parsed_fields.get("ssid") or "(unknown)"
    hidden = bool(parsed_fields.get("hidden"))
    auth = parsed_fields.get("authentication", "nopass")

    reasons = []
    recommendations = [
        "Only connect to WiFi networks you recognize and trust.",
        "Rogue access points can use QR codes to trick you into joining a malicious network.",
    ]
    impact = 0
    severity = Severity.INFO
    message = f"WiFi network '{ssid}' ({auth})."

    if hidden:
        reasons.append("✔ This QR code configures a hidden (non-broadcasting) network.")
        impact = -5
        severity = Severity.LOW
        message += " Network is hidden."

    if auth.lower() == "nopass":
        reasons.append("✔ This network has no password — traffic on it is typically unencrypted.")
        impact -= 10
        severity = Severity.LOW
        recommendations.append("Avoid entering sensitive information while connected to an open network.")

    score = max(0, min(100, 100 + impact))

    rule_results = [
        RuleResult(
            rule="wifi_analysis",
            label="WiFi Analysis",
            triggered=bool(reasons),
            impact=impact,
            severity=severity,
            message=message,
        )
    ]

    return score, RiskLevel.from_score(score), reasons, recommendations, rule_results
