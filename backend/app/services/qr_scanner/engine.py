from datetime import datetime, timezone

from app.services.qr_scanner.content_type import detect_and_parse, redact_wifi_raw_content
from app.services.qr_scanner.rules import HANDLERS
from app.services.qr_scanner.types import ContentType, QRReport


def analyze_qr_content(raw_content: str) -> QRReport:
    content_type, parsed_fields = detect_and_parse(raw_content)
    handler = HANDLERS[content_type]

    trust_score, risk_level, reasons, recommendations, rule_results = handler(parsed_fields)

    # The WIFI raw string embeds the plaintext password (`P:...;`) — every
    # consumer of this report (API response, persisted history row) must
    # only ever see the redacted form, never the original.
    stored_raw_content = redact_wifi_raw_content(raw_content) if content_type == ContentType.WIFI else raw_content

    return QRReport(
        content_type=content_type,
        raw_content=stored_raw_content,
        parsed_fields=parsed_fields,
        trust_score=trust_score,
        risk_level=risk_level,
        reasons=reasons,
        recommendations=recommendations,
        rule_results=rule_results,
        scanned_at=datetime.now(timezone.utc),
    )
