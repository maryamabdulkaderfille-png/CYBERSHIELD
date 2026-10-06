"""Parses raw email source (RFC 822 / .eml) into an EmailContext.

Deliberately never writes anything to disk: uploaded files and pasted text
are read into memory, parsed, and discarded. Attachment *content* is never
decoded either — only the filename/content-type metadata rules need — which
sidesteps decompression-bomb-style resource exhaustion from attachment
payloads entirely.

Python's `email` package is very tolerant of malformed input by design (it
records problems as `.defects` rather than raising), so pasted plain body
text with no headers at all parses fine too: `sender`/`subject` just come
back None, which the sender-analysis rule already treats as a finding.
"""

import re
from email import message_from_bytes, message_from_string, policy
from email.utils import parseaddr
from html.parser import HTMLParser

from app.services.email_scanner.types import EmailAttachment, EmailContext

MAX_EXTRACTED_LINKS = 30

_URL_RE = re.compile(r"""(?i)\bhttps?://[^\s"'<>\)\]]+""")


class _TextExtractor(HTMLParser):
    """Strips tags for keyword-scanning purposes only (not for display)."""

    def __init__(self):
        super().__init__()
        self._chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        self._chunks.append(data)

    def text(self) -> str:
        return " ".join(self._chunks)


def _html_to_text(html_content: str) -> str:
    extractor = _TextExtractor()
    try:
        extractor.feed(html_content)
    except Exception:
        return html_content
    return extractor.text()


def _get_part_text(part) -> str:
    try:
        content = part.get_content()
        return content if isinstance(content, str) else str(content)
    except Exception:
        payload = part.get_payload(decode=True)
        if payload is None:
            return ""
        charset = part.get_content_charset() or "utf-8"
        try:
            return payload.decode(charset, errors="replace")
        except (LookupError, UnicodeDecodeError):
            return payload.decode("utf-8", errors="replace")


def _extract_links(*sources: str) -> list[str]:
    seen: list[str] = []
    for source in sources:
        if not source:
            continue
        for match in _URL_RE.finditer(source):
            url = match.group(0).rstrip(".,;:!?")
            if url not in seen:
                seen.append(url)
            if len(seen) >= MAX_EXTRACTED_LINKS:
                return seen
    return seen


def parse_email_source(raw: bytes | str) -> EmailContext:
    if isinstance(raw, bytes):
        msg = message_from_bytes(raw, policy=policy.default)
    else:
        msg = message_from_string(raw, policy=policy.default)

    display_name, sender_email = parseaddr(msg.get("From", "") or "")
    display_name = display_name.strip() or None
    sender_email = sender_email.strip() or None
    subject = msg.get("Subject")
    subject = str(subject).strip() if subject else None

    body_text = ""
    body_html: str | None = None
    attachments: list[EmailAttachment] = []
    defects: list[str] = []

    parts = msg.walk() if msg.is_multipart() else [msg]
    for part in parts:
        defects.extend(str(d) for d in getattr(part, "defects", []))

        if part.is_multipart():
            continue

        filename = part.get_filename()
        disposition = part.get_content_disposition()
        if disposition == "attachment" or (filename and disposition != "inline"):
            attachments.append(EmailAttachment(filename=filename or "unnamed", content_type=part.get_content_type()))
            continue

        content_type = part.get_content_type()
        if content_type == "text/plain" and not body_text:
            body_text = _get_part_text(part)
        elif content_type == "text/html" and body_html is None:
            body_html = _get_part_text(part)

    if not body_text and body_html:
        body_text = _html_to_text(body_html)

    links = _extract_links(body_text, body_html or "")

    headers = {key: str(value) for key, value in msg.items()}

    return EmailContext(
        sender_display_name=display_name,
        sender_email=sender_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        links=links,
        attachments=attachments,
        headers=headers,
        parse_defects=defects,
    )
