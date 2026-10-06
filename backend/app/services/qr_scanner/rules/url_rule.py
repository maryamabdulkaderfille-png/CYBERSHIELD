"""QR codes containing a URL are hard-routed to the full Phase 2 URL
Scanner — no URL analysis logic is duplicated here."""

import dataclasses

from app.services.qr_scanner.types import RuleResult
from app.services.url_scanner.engine import scan_url


def analyze(parsed_fields: dict):
    report = scan_url(parsed_fields["url"])
    rule_results = [RuleResult(**dataclasses.asdict(r)) for r in report.rule_results]
    return report.trust_score, report.risk_level, report.reasons, report.recommendations, rule_results
