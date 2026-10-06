"""Very light-touch heuristics for common phishing writing patterns —
excessive punctuation/shouting and a couple of stock scam phrasings.

Deliberately low weight and high bar to trigger: real emails from
non-native speakers or enthusiastic marketers shouldn't get penalized
significantly, so this rule should never be a major factor in the score.
"""

import re

from app.services.email_scanner.types import EmailContext, RuleResult, Severity

_REPEATED_PUNCTUATION_RE = re.compile(r"[!?]{2,}")
_SCAM_PHRASES = ["kindly", "revert back", "do the needful", "beneficiary"]


def _shouting_word_ratio(text: str) -> float:
    words = [w for w in re.findall(r"[A-Za-z]+", text) if len(w) >= 4]
    if not words:
        return 0.0
    shouting = [w for w in words if w.isupper()]
    return len(shouting) / len(words)


def evaluate(ctx: EmailContext) -> RuleResult:
    body = ctx.body_text or ""
    findings: list[str] = []
    impact = 0

    if _REPEATED_PUNCTUATION_RE.search(body):
        findings.append("repeated exclamation/question marks")
        impact -= 2

    if _shouting_word_ratio(body) > 0.15:
        findings.append("unusually high proportion of ALL-CAPS words")
        impact -= 2

    matched_phrases = [p for p in _SCAM_PHRASES if p in body.lower()]
    if matched_phrases:
        findings.append(f"uses phrasing common in scam emails ({', '.join(matched_phrases)})")
        impact -= 2

    if not findings:
        return RuleResult(
            rule="grammar_heuristics",
            label="Grammar Heuristics",
            triggered=False,
            impact=0,
            severity=Severity.INFO,
            message="No suspicious writing patterns detected.",
        )

    return RuleResult(
        rule="grammar_heuristics",
        label="Grammar Heuristics",
        triggered=True,
        impact=max(impact, -5),
        severity=Severity.INFO,
        message="Minor writing-pattern signals: " + "; ".join(findings) + ".",
    )
