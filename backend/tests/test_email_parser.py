from app.services.email_scanner.parser import parse_email_source

PHISHING_EML = """From: "PayPal Support" <support@mail-secure-paypal.com>
Subject: Urgent: Your Account Will Be Suspended
Content-Type: multipart/mixed; boundary="XYZ"

--XYZ
Content-Type: text/plain; charset="utf-8"

Dear Customer,

We have detected unusual activity on your account. You must verify your identity immediately or your account will be suspended within 24 hours.

Please click the link below to confirm your information:
http://paypa1-secure-login.com/verify

Act now to avoid permanent suspension.

Thank you,
PayPal Security Team

--XYZ
Content-Type: application/octet-stream; name="invoice.pdf.exe"
Content-Disposition: attachment; filename="invoice.pdf.exe"
Content-Transfer-Encoding: base64

QQ==
--XYZ--
"""


def test_parses_sender_display_name_and_email():
    ctx = parse_email_source(PHISHING_EML)
    assert ctx.sender_display_name == "PayPal Support"
    assert ctx.sender_email == "support@mail-secure-paypal.com"


def test_parses_subject():
    ctx = parse_email_source(PHISHING_EML)
    assert ctx.subject == "Urgent: Your Account Will Be Suspended"


def test_extracts_body_text():
    ctx = parse_email_source(PHISHING_EML)
    assert "unusual activity" in ctx.body_text
    assert "Dear Customer" in ctx.body_text


def test_extracts_links():
    ctx = parse_email_source(PHISHING_EML)
    assert ctx.links == ["http://paypa1-secure-login.com/verify"]


def test_extracts_attachments():
    ctx = parse_email_source(PHISHING_EML)
    assert len(ctx.attachments) == 1
    assert ctx.attachments[0].filename == "invoice.pdf.exe"


def test_parses_bytes_input():
    ctx = parse_email_source(PHISHING_EML.encode("utf-8"))
    assert ctx.sender_email == "support@mail-secure-paypal.com"


def test_missing_headers_degrades_gracefully():
    """Plain pasted body text with no headers at all shouldn't crash — it
    should just come back with no sender/subject, which sender_analysis
    already treats as a finding."""
    ctx = parse_email_source("Hey, just checking in about tomorrow's meeting. See you then!")
    assert ctx.sender_email is None
    assert ctx.subject is None
    assert "meeting" in ctx.body_text


def test_empty_string_does_not_crash():
    ctx = parse_email_source("")
    assert ctx.sender_email is None


def test_malformed_mime_does_not_crash():
    malformed = 'From: broken\nContent-Type: multipart/mixed; boundary="X"\n\nNo boundary markers at all here.'
    ctx = parse_email_source(malformed)
    assert isinstance(ctx.body_text, str)


def test_html_only_email_falls_back_to_derived_text():
    html_email = (
        "From: sender@example.com\nSubject: Hi\nContent-Type: text/html; charset=utf-8\n\n"
        "<html><body><p>Hello <b>there</b></p></body></html>"
    )
    ctx = parse_email_source(html_email)
    assert ctx.body_html is not None
    assert "Hello" in ctx.body_text
    assert "<b>" not in ctx.body_text


def test_extracts_links_from_html_href():
    html_email = (
        "From: sender@example.com\nSubject: Hi\nContent-Type: text/html; charset=utf-8\n\n"
        '<html><body><a href="https://phish.example/login">Click here</a></body></html>'
    )
    ctx = parse_email_source(html_email)
    assert "https://phish.example/login" in ctx.links


def test_caps_number_of_extracted_links():
    many_links = " ".join(f"http://example.com/{i}" for i in range(100))
    email_with_many_links = f"From: sender@example.com\nSubject: Hi\n\n{many_links}"
    ctx = parse_email_source(email_with_many_links)
    from app.services.email_scanner.parser import MAX_EXTRACTED_LINKS

    assert len(ctx.links) == MAX_EXTRACTED_LINKS


def test_inline_image_is_not_treated_as_attachment():
    inline_email = (
        "From: sender@example.com\nSubject: Hi\nContent-Type: multipart/mixed; boundary=X\n\n"
        "--X\nContent-Type: text/plain\n\nHello\n--X\n"
        'Content-Type: image/png\nContent-Disposition: inline; filename="logo.png"\n'
        "Content-Transfer-Encoding: base64\n\nQQ==\n--X--"
    )
    ctx = parse_email_source(inline_email)
    assert ctx.attachments == []
