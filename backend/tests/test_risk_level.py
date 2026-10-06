import pytest

from app.constants import RiskLevel


@pytest.mark.parametrize(
    "score,expected",
    [
        (100, RiskLevel.SAFE),
        (90, RiskLevel.SAFE),
        (89, RiskLevel.LOW_RISK),
        (70, RiskLevel.LOW_RISK),
        (69, RiskLevel.SUSPICIOUS),
        (40, RiskLevel.SUSPICIOUS),
        (39, RiskLevel.DANGEROUS),
        (0, RiskLevel.DANGEROUS),
    ],
)
def test_from_score_boundaries(score, expected):
    assert RiskLevel.from_score(score) == expected
