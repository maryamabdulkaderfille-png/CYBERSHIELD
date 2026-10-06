"""Small, dependency-free shared constants.

Lives outside both `models` and `services` so either layer can import it
without creating a circular dependency between them.
"""


class RiskLevel:
    SAFE = "Safe"
    LOW_RISK = "Low Risk"
    SUSPICIOUS = "Suspicious"
    DANGEROUS = "Dangerous"
    ALL = (SAFE, LOW_RISK, SUSPICIOUS, DANGEROUS)

    @staticmethod
    def from_score(score: int) -> str:
        if score >= 90:
            return RiskLevel.SAFE
        if score >= 70:
            return RiskLevel.LOW_RISK
        if score >= 40:
            return RiskLevel.SUSPICIOUS
        return RiskLevel.DANGEROUS
