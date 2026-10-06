from app.services.qr_scanner.content_type import detect_and_parse, redact_wifi_raw_content
from app.services.qr_scanner.types import ContentType


def test_detects_url():
    content_type, fields = detect_and_parse("https://example.com/login")
    assert content_type == ContentType.URL
    assert fields["url"] == "https://example.com/login"


def test_detects_bare_www_as_url():
    content_type, fields = detect_and_parse("www.example.com")
    assert content_type == ContentType.URL
    assert fields["url"] == "https://www.example.com"


def test_detects_mailto():
    content_type, fields = detect_and_parse("mailto:support@example.com?subject=Hello&body=Hi%20there")
    assert content_type == ContentType.EMAIL
    assert fields["address"] == "support@example.com"
    assert fields["subject"] == "Hello"
    assert fields["body"] == "Hi there"


def test_detects_bare_mailto_no_query():
    content_type, fields = detect_and_parse("mailto:someone@example.com")
    assert content_type == ContentType.EMAIL
    assert fields["address"] == "someone@example.com"
    assert fields["subject"] is None


def test_detects_tel():
    content_type, fields = detect_and_parse("tel:+15551234567")
    assert content_type == ContentType.PHONE
    assert fields["number"] == "+15551234567"


def test_detects_sms():
    content_type, fields = detect_and_parse("sms:+15551234567?body=Verify%20now")
    assert content_type == ContentType.SMS
    assert fields["number"] == "+15551234567"
    assert fields["message"] == "Verify now"


def test_detects_smsto_legacy_format():
    content_type, fields = detect_and_parse("SMSTO:+15551234567:Urgent message here")
    assert content_type == ContentType.SMS
    assert fields["number"] == "+15551234567"
    assert fields["message"] == "Urgent message here"


def test_detects_wifi():
    content_type, fields = detect_and_parse("WIFI:S:HomeNetwork;T:WPA;P:secret123;H:false;;")
    assert content_type == ContentType.WIFI
    assert fields["ssid"] == "HomeNetwork"
    assert fields["authentication"] == "WPA"
    assert fields["hidden"] is False
    assert fields["has_password"] is True
    assert "P" not in fields
    assert "password" not in fields


def test_wifi_hidden_network():
    content_type, fields = detect_and_parse("WIFI:S:Secret;T:nopass;H:true;;")
    assert content_type == ContentType.WIFI
    assert fields["hidden"] is True
    assert fields["has_password"] is False


def test_detects_crypto_uri():
    content_type, fields = detect_and_parse("bitcoin:1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa?amount=0.1")
    assert content_type == ContentType.CRYPTO
    assert fields["network"] == "Bitcoin (BTC)"
    assert fields["is_valid_format"] is True


def test_detects_raw_btc_address():
    content_type, fields = detect_and_parse("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    assert content_type == ContentType.CRYPTO
    assert "Bitcoin" in fields["network"]


def test_detects_raw_eth_address():
    content_type, fields = detect_and_parse("0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
    assert content_type == ContentType.CRYPTO
    assert "Ethereum" in fields["network"]


def test_detects_invalid_crypto_uri_format():
    content_type, fields = detect_and_parse("bitcoin:not-a-valid-address")
    assert content_type == ContentType.CRYPTO
    assert fields["is_valid_format"] is False


def test_detects_plain_text():
    content_type, fields = detect_and_parse("Just a regular note, nothing special.")
    assert content_type == ContentType.PLAIN_TEXT
    assert fields["text"] == "Just a regular note, nothing special."


def test_detects_unknown_for_empty_content():
    content_type, fields = detect_and_parse("   ")
    assert content_type == ContentType.UNKNOWN
    assert fields == {}


def test_redact_wifi_password():
    redacted = redact_wifi_raw_content("WIFI:S:Home;T:WPA;P:supersecret;H:false;;")
    assert "supersecret" not in redacted
    assert "[REDACTED]" in redacted
    assert "Home" in redacted


def test_redact_wifi_password_noop_for_non_wifi():
    content = "https://example.com"
    assert redact_wifi_raw_content(content) == content
