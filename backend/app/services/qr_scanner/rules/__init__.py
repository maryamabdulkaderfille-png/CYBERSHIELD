from app.services.qr_scanner.rules import (
    crypto_analysis,
    email_rule,
    phone_analysis,
    plain_text_analysis,
    sms_analysis,
    unknown_analysis,
    url_rule,
    wifi_analysis,
)
from app.services.qr_scanner.types import ContentType

# Dispatch table, not a uniform "run every rule" list like the URL/email
# scanners: QR content types are mutually exclusive (a QR code is exactly
# one of URL/email/phone/... at a time), so exactly one handler applies per
# scan rather than many independent rules contributing to one score.
HANDLERS = {
    ContentType.URL: url_rule.analyze,
    ContentType.EMAIL: email_rule.analyze,
    ContentType.PHONE: phone_analysis.analyze,
    ContentType.SMS: sms_analysis.analyze,
    ContentType.WIFI: wifi_analysis.analyze,
    ContentType.CRYPTO: crypto_analysis.analyze,
    ContentType.PLAIN_TEXT: plain_text_analysis.analyze,
    ContentType.UNKNOWN: unknown_analysis.analyze,
}
