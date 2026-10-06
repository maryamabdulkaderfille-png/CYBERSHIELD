from app.services.email_scanner.engine import analyze_email
from app.services.email_scanner.parser import parse_email_source
from app.services.url_scanner.types import RiskLevel

PHISHING_EML = """From: "PayPal Support" <support@mail-secure-paypal.com>
Subject: Urgent: Your Account Will Be Suspended

Dear Customer,

We have detected unusual activity on your account. You must verify your identity immediately or your account will be suspended within 24 hours.

Please click the link below to confirm your information:
http://paypa1-secure-login.com/verify

Act now to avoid permanent suspension.
"""

CLEAN_EMAIL = """From: Jane Doe <jane@example.com>
Subject: Lunch tomorrow?

Hi Sarah,

Are you free for lunch tomorrow around noon? Let me know what works for you.

Thanks,
Jane
"""


def test_clean_email_scores_high(app):
    with app.app_context():
        ctx = parse_email_source(CLEAN_EMAIL)
        report = analyze_email(ctx)
    assert report.trust_score >= 90
    assert report.risk_level == RiskLevel.SAFE
    assert report.reasons == []


def test_phishing_email_scores_low(app):
    with app.app_context():
        ctx = parse_email_source(PHISHING_EML)
        report = analyze_email(ctx)
    assert report.trust_score < 40
    assert report.risk_level == RiskLevel.DANGEROUS
    assert len(report.reasons) >= 4
    assert len(report.recommendations) > 0
    assert report.sender_email == "support@mail-secure-paypal.com"
    assert report.subject == "Urgent: Your Account Will Be Suspended"


def test_report_includes_link_findings(app):
    with app.app_context():
        ctx = parse_email_source(PHISHING_EML)
        report = analyze_email(ctx)
    assert len(report.links) == 1
    assert report.links[0].url == "http://paypa1-secure-login.com/verify"


def test_report_includes_attachment_findings(app):
    eml_with_attachment = (
        'From: a@example.com\nSubject: Invoice\nContent-Type: multipart/mixed; boundary="X"\n\n'
        "--X\nContent-Type: text/plain\n\nSee attached.\n--X\n"
        'Content-Type: application/octet-stream; name="invoice.pdf.exe"\n'
        'Content-Disposition: attachment; filename="invoice.pdf.exe"\n'
        "Content-Transfer-Encoding: base64\n\nQQ==\n--X--"
    )
    with app.app_context():
        ctx = parse_email_source(eml_with_attachment)
        report = analyze_email(ctx)
    assert len(report.attachments) == 1
    assert report.attachments[0].is_dangerous is True


def test_score_never_goes_below_zero_or_above_hundred(app):
    with app.app_context():
        ctx = parse_email_source(
            "From: \"PayPal Bank Security\" <a@gmail.com>\n"
            "Subject: URGENT Verify Suspended Payment Failed Security Alert Password Reset\n\n"
            "Dear Customer, act now immediately within 24 hours final warning urgent response required. "
            "Account suspension payment failure security breach verify your identity login required "
            "unauthorized access unusual activity. http://192.168.1.1/login-verify-secure-bank-wallet"
        )
        report = analyze_email(ctx)
    assert 0 <= report.trust_score <= 100


def test_no_sender_or_subject_still_produces_a_report(app):
    with app.app_context():
        ctx = parse_email_source("Just some plain text with no headers at all.")
        report = analyze_email(ctx)
    assert report.sender_email is None
    assert any("sender" in reason.lower() for reason in report.reasons)
