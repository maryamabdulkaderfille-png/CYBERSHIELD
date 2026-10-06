from app.services.qr_scanner.engine import analyze_qr_content
from app.services.qr_scanner.types import ContentType
from app.services.url_scanner.types import RiskLevel


def test_url_content_reuses_url_scanner(app):
    with app.app_context():
        report = analyze_qr_content("https://paypaI.com/signin")
    assert report.content_type == ContentType.URL
    assert report.risk_level in {RiskLevel.SUSPICIOUS, RiskLevel.DANGEROUS}
    assert any("typosquatting" in r.lower() for r in report.reasons)


def test_clean_url_content_scores_high(app):
    with app.app_context():
        report = analyze_qr_content("https://example.com")
    assert report.trust_score >= 90
    assert report.risk_level == RiskLevel.SAFE


def test_email_content_reuses_email_scanner(app):
    with app.app_context():
        report = analyze_qr_content("mailto:support@gmail.com?subject=URGENT%20Verify%20Your%20Account")
    assert report.content_type == ContentType.EMAIL
    assert any("phishing-lure" in r.lower() or "subject" in r.lower() for r in report.reasons)


def test_phone_premium_rate_flagged():
    report = analyze_qr_content("tel:+19005551234")
    assert report.content_type == ContentType.PHONE
    assert report.risk_level == "Dangerous"


def test_phone_normal_number_safe():
    report = analyze_qr_content("tel:+15551234567")
    assert report.content_type == ContentType.PHONE
    assert report.risk_level == "Safe"


def test_sms_with_phishing_language():
    report = analyze_qr_content("sms:+15551234567?body=Your account is suspended, act now immediately")
    assert report.content_type == ContentType.SMS
    assert len(report.reasons) > 0
    assert report.trust_score < 100


def test_sms_with_no_message():
    report = analyze_qr_content("sms:+15551234567")
    assert report.content_type == ContentType.SMS
    assert report.risk_level == "Safe"


def test_wifi_password_never_in_report():
    report = analyze_qr_content("WIFI:S:Home;T:WPA;P:supersecret123;H:false;;")
    assert report.content_type == ContentType.WIFI
    assert "supersecret123" not in report.raw_content
    assert "supersecret123" not in str(report.parsed_fields)
    assert "supersecret123" not in " ".join(report.reasons)


def test_wifi_open_network_flagged():
    report = analyze_qr_content("WIFI:S:OpenNet;T:nopass;H:false;;")
    assert report.content_type == ContentType.WIFI
    assert any("no password" in r.lower() or "unencrypted" in r.lower() for r in report.reasons)


def test_crypto_valid_address():
    report = analyze_qr_content("bitcoin:1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    assert report.content_type == ContentType.CRYPTO
    assert report.risk_level == "Low Risk"


def test_crypto_invalid_address_is_dangerous():
    report = analyze_qr_content("bitcoin:not-a-real-address")
    assert report.content_type == ContentType.CRYPTO
    assert report.risk_level == "Dangerous"


def test_plain_text_is_safe():
    report = analyze_qr_content("Just a note to self.")
    assert report.content_type == ContentType.PLAIN_TEXT
    assert report.risk_level == "Safe"
    assert report.trust_score == 100


def test_unknown_empty_content_is_suspicious():
    report = analyze_qr_content("   ")
    assert report.content_type == ContentType.UNKNOWN
    assert report.risk_level == "Suspicious"


def test_score_always_within_bounds(app):
    with app.app_context():
        for content in [
            "https://8.8.4.4/login-verify-secure-bank-wallet-paypal",
            "tel:+1900",
            "WIFI:S:x;T:nopass;H:true;;",
            "bitcoin:bad",
            "",
        ]:
            report = analyze_qr_content(content)
            assert 0 <= report.trust_score <= 100
