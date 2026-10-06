""""Why is this dangerous?" plain-language explanation (Phase 9, Feature 7).

This is NOT a call to an external AI/LLM API — no such integration exists in
this project, and "Do NOT implement AI / machine learning" has been an
explicit instruction in prior phases. Instead, this composes a short,
human-readable narrative entirely from the existing detection engine's own
already-computed rule results (`analysis_details.rules` / `scan_result.reasons`)
— the same data the report/reasons list already shows, just reordered by
severity and phrased as a summary instead of a bullet list. No new detection
logic, no fabricated content: every point here is a rule that genuinely
triggered on this exact scan.
"""

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
MAX_POINTS = 5


def generate_explanation(risk: str, trust_score: int, reasons: list[str], rules: list[dict]) -> dict:
    triggered = [rule for rule in rules if rule.get("triggered")]
    triggered.sort(key=lambda rule: _SEVERITY_ORDER.get(rule.get("severity"), len(_SEVERITY_ORDER)))

    points = [rule["message"] for rule in triggered[:MAX_POINTS] if rule.get("message")]
    if not points:
        points = list(reasons[:MAX_POINTS])

    if risk == "Dangerous":
        summary = "This site shows multiple strong signs of a phishing or scam attempt."
        recommendation = "Do not enter passwords, payment details, or personal information on this site."
    elif risk == "Suspicious":
        summary = "This site shows some signs that are worth being cautious about."
        recommendation = "Proceed carefully, and avoid entering sensitive information unless you're confident this is the real site."
    else:
        summary = "No significant phishing indicators were found for this scan."
        recommendation = "Still use your own judgment — a good score doesn't guarantee a site is completely safe."

    return {
        "risk": risk,
        "trust_score": trust_score,
        "summary": summary,
        "points": points,
        "recommendation": recommendation,
    }
