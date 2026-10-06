from app.services.email_scanner.rules import (
    attachment_analysis,
    display_name_impersonation,
    grammar_heuristics,
    greeting_analysis,
    html_analysis,
    link_analysis,
    sender_analysis,
    subject_analysis,
    threat_language,
    urgency_detection,
)
from app.services.email_scanner.types import EmailAttachment, EmailContext


def make_context(**overrides) -> EmailContext:
    defaults = dict(
        sender_display_name=None,
        sender_email=None,
        subject=None,
        body_text="",
        body_html=None,
        links=[],
        attachments=[],
        headers={},
        parse_defects=[],
    )
    defaults.update(overrides)
    return EmailContext(**defaults)


# --- sender_analysis ---


def test_sender_analysis_flags_missing_sender():
    result = sender_analysis.evaluate(make_context(sender_email=None))
    assert result.triggered
    assert result.impact < 0


def test_sender_analysis_flags_malformed_sender():
    result = sender_analysis.evaluate(make_context(sender_email="not-an-email"))
    assert result.triggered


def test_sender_analysis_flags_free_email_as_organization():
    result = sender_analysis.evaluate(
        make_context(sender_display_name="PayPal Support", sender_email="support@gmail.com")
    )
    assert result.triggered
    assert result.impact < 0


def test_sender_analysis_passes_normal_sender():
    result = sender_analysis.evaluate(
        make_context(sender_display_name="Jane Doe", sender_email="jane@example.com")
    )
    assert not result.triggered


# --- subject_analysis ---


def test_subject_analysis_flags_keywords():
    result = subject_analysis.evaluate(make_context(subject="URGENT: Verify your account now"))
    assert result.triggered


def test_subject_analysis_passes_normal_subject():
    result = subject_analysis.evaluate(make_context(subject="Lunch tomorrow?"))
    assert not result.triggered


def test_subject_analysis_handles_missing_subject():
    result = subject_analysis.evaluate(make_context(subject=None))
    assert not result.triggered


# --- greeting_analysis ---


def test_greeting_analysis_flags_generic_greeting():
    result = greeting_analysis.evaluate(make_context(body_text="Dear Customer, please update your info."))
    assert result.triggered


def test_greeting_analysis_passes_personalized_greeting():
    result = greeting_analysis.evaluate(make_context(body_text="Hi Sarah, thanks for reaching out."))
    assert not result.triggered


# --- urgency_detection ---


def test_urgency_detection_flags_pressure_language():
    result = urgency_detection.evaluate(make_context(body_text="You must act now, within 24 hours!"))
    assert result.triggered


def test_urgency_detection_passes_calm_language():
    result = urgency_detection.evaluate(make_context(body_text="Let me know whenever is convenient."))
    assert not result.triggered


# --- threat_language ---


def test_threat_language_flags_threats():
    result = threat_language.evaluate(make_context(body_text="Your account suspension is imminent."))
    assert result.triggered


def test_threat_language_passes_neutral_text():
    result = threat_language.evaluate(make_context(body_text="Attached is the report you asked for."))
    assert not result.triggered


# --- display_name_impersonation ---


def test_display_name_impersonation_flags_brand_domain_mismatch():
    result = display_name_impersonation.evaluate(
        make_context(sender_display_name="Microsoft Account Team", sender_email="alert@micro-soft-verify.com")
    )
    assert result.triggered
    assert result.detail == "microsoft"


def test_display_name_impersonation_passes_legitimate_domain():
    result = display_name_impersonation.evaluate(
        make_context(sender_display_name="Microsoft Account Team", sender_email="alert@microsoft.com")
    )
    assert not result.triggered


def test_display_name_impersonation_passes_no_brand_mentioned():
    result = display_name_impersonation.evaluate(
        make_context(sender_display_name="Jane Doe", sender_email="jane@example.com")
    )
    assert not result.triggered


# --- attachment_analysis ---


def test_attachment_analysis_flags_dangerous_extension():
    result = attachment_analysis.evaluate(make_context(attachments=[EmailAttachment(filename="update.exe")]))
    assert result.triggered


def test_attachment_analysis_flags_double_extension():
    result = attachment_analysis.evaluate(make_context(attachments=[EmailAttachment(filename="invoice.pdf.exe")]))
    assert result.triggered
    assert "Double extension" in result.message


def test_attachment_analysis_passes_safe_attachment():
    result = attachment_analysis.evaluate(make_context(attachments=[EmailAttachment(filename="invoice.pdf")]))
    assert not result.triggered


def test_attachment_analysis_passes_no_attachments():
    result = attachment_analysis.evaluate(make_context(attachments=[]))
    assert not result.triggered


# --- html_analysis ---


def test_html_analysis_flags_script_tag():
    result = html_analysis.evaluate(make_context(body_html="<html><script>evil()</script></html>"))
    assert result.triggered


def test_html_analysis_flags_form_tag():
    result = html_analysis.evaluate(make_context(body_html='<form action="http://evil.com"><input/></form>'))
    assert result.triggered


def test_html_analysis_flags_hidden_elements():
    result = html_analysis.evaluate(make_context(body_html='<div style="display:none">secret tracking</div>'))
    assert result.triggered


def test_html_analysis_passes_plain_html():
    result = html_analysis.evaluate(make_context(body_html="<html><body><p>Hello there</p></body></html>"))
    assert not result.triggered


def test_html_analysis_not_applicable_without_html():
    result = html_analysis.evaluate(make_context(body_html=None))
    assert not result.triggered


# --- grammar_heuristics (low weight) ---


def test_grammar_heuristics_low_weight_even_when_triggered():
    result = grammar_heuristics.evaluate(make_context(body_text="ACT NOW!!! KINDLY REVERT BACK ASAP!!!"))
    assert result.triggered
    assert result.impact >= -5  # deliberately capped low


def test_grammar_heuristics_passes_normal_text():
    result = grammar_heuristics.evaluate(make_context(body_text="Thanks for your help with this."))
    assert not result.triggered


# --- link_analysis ---


def test_link_analysis_passes_no_links():
    result = link_analysis.evaluate(make_context(links=[]))
    assert not result.triggered


def test_link_analysis_flags_dangerous_link(app):
    with app.app_context():
        result = link_analysis.evaluate(make_context(links=["http://192.168.10.2/login-verify-account"]))
    assert result.triggered
    assert result.severity == "critical"


def test_link_analysis_passes_clean_link(app):
    with app.app_context():
        result = link_analysis.evaluate(make_context(links=["https://example.com"]))
    assert not result.triggered
