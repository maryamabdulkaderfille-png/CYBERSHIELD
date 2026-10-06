"""Classifies decoded QR text into one of the supported content types and
extracts its structured fields. Pure parsing — no analysis/scoring here."""

import re
from urllib.parse import parse_qs, unquote, urlparse

from app.services.qr_scanner.types import ContentType

_WIFI_FIELD_RE = re.compile(r"(?<!\\)([A-Z]):((?:\\.|[^;\\])*);")
_WIFI_PASSWORD_FIELD_RE = re.compile(r"(?<!\\)(P:)((?:\\.|[^;\\])*)(;)")


def redact_wifi_raw_content(raw_content: str) -> str:
    """The raw decoded string for a WIFI QR code (`WIFI:S:...;P:secret;;`)
    contains the plaintext password. Never store or return that verbatim —
    only this redacted form should ever reach the database or an API
    response."""
    return _WIFI_PASSWORD_FIELD_RE.sub(r"\1[REDACTED];", raw_content)


def _unescape_wifi(value: str) -> str:
    return re.sub(r"\\(.)", r"\1", value)


def detect_and_parse(raw_content: str) -> tuple[str, dict]:
    content = raw_content.strip()

    if not content:
        return ContentType.UNKNOWN, {}

    lower = content.lower()

    if lower.startswith(("http://", "https://")):
        return ContentType.URL, {"url": content}
    if lower.startswith("www."):
        return ContentType.URL, {"url": f"https://{content}"}

    if lower.startswith("mailto:"):
        return ContentType.EMAIL, _parse_mailto(content)

    if lower.startswith("tel:"):
        return ContentType.PHONE, {"number": content[len("tel:"):].strip()}

    if lower.startswith("smsto:"):
        rest = content[len("smsto:"):]
        number, _, message = rest.partition(":")
        return ContentType.SMS, {"number": number.strip(), "message": message.strip() or None}
    if lower.startswith("sms:"):
        return ContentType.SMS, _parse_sms(content)

    if lower.startswith("wifi:"):
        return ContentType.WIFI, _parse_wifi(content)

    crypto_fields = _parse_crypto(content)
    if crypto_fields:
        return ContentType.CRYPTO, crypto_fields

    return ContentType.PLAIN_TEXT, {"text": content}


def _parse_mailto(content: str) -> dict:
    parsed = urlparse(content)
    address = unquote(parsed.path)
    query = parse_qs(parsed.query)
    return {
        "address": address,
        "subject": query.get("subject", [None])[0],
        "body": query.get("body", [None])[0],
    }


def _parse_sms(content: str) -> dict:
    without_scheme = content[len("sms:"):]
    parsed = urlparse("sms://" + without_scheme)
    number = parsed.netloc or without_scheme.split("?")[0]
    query = parse_qs(parsed.query)
    return {"number": number.strip(), "message": query.get("body", [None])[0]}


_CRYPTO_SCHEMES = {
    "bitcoin": "Bitcoin (BTC)",
    "bitcoincash": "Bitcoin Cash (BCH)",
    "ethereum": "Ethereum (ETH)",
    "litecoin": "Litecoin (LTC)",
    "dogecoin": "Dogecoin (DOGE)",
    "ripple": "XRP",
    "tron": "TRON (TRX)",
}

_ADDRESS_PATTERNS = [
    (re.compile(r"^0x[0-9a-fA-F]{40}$"), "Ethereum (ETH) / EVM-compatible"),
    (re.compile(r"^(bc1|[13])[a-km-zA-HJ-NP-Z1-9]{25,60}$"), "Bitcoin (BTC)"),
    (re.compile(r"^(ltc1|[LM3])[a-km-zA-HJ-NP-Z1-9]{25,60}$"), "Litecoin (LTC)"),
    (re.compile(r"^D[5-9A-HJ-NP-U][1-9A-HJ-NP-Za-km-z]{32}$"), "Dogecoin (DOGE)"),
    (re.compile(r"^T[A-Za-z1-9]{33}$"), "TRON (TRX)"),
    (re.compile(r"^r[0-9a-zA-Z]{24,34}$"), "XRP"),
]


def _parse_crypto(content: str) -> dict | None:
    if ":" in content:
        scheme, _, rest = content.partition(":")
        scheme_lower = scheme.lower()
        if scheme_lower in _CRYPTO_SCHEMES:
            parsed = urlparse(content)
            address = parsed.path or rest.split("?")[0]
            return {
                "network": _CRYPTO_SCHEMES[scheme_lower],
                "address": address,
                "is_valid_format": _looks_like_valid_address(address),
            }
        return None

    for pattern, network in _ADDRESS_PATTERNS:
        if pattern.match(content):
            return {"network": network, "address": content, "is_valid_format": True}

    return None


def _looks_like_valid_address(address: str) -> bool:
    if not address:
        return False
    for pattern, _network in _ADDRESS_PATTERNS:
        if pattern.match(address):
            return True
    # Ethereum-style addresses are also valid inside an `ethereum:` URI.
    return bool(re.match(r"^0x[0-9a-fA-F]{40}$", address))


def _parse_wifi(content: str) -> dict:
    body = content[len("WIFI:"):]
    fields: dict[str, str] = {}
    for match in _WIFI_FIELD_RE.finditer(body):
        key, value = match.group(1), match.group(2)
        fields[key] = _unescape_wifi(value)

    return {
        "ssid": fields.get("S"),
        "authentication": fields.get("T", "nopass"),
        "hidden": fields.get("H", "false").lower() == "true",
        "has_password": bool(fields.get("P")),
        # Deliberately not included: the raw password itself — see
        # rules/wifi_analysis.py and the API response, which never expose it.
    }
