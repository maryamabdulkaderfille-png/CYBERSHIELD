import os

from app.utils.errors import APIError

MAX_EMAIL_TEXT_LENGTH = 200_000  # ~200 KB of pasted source
# Werkzeug 3.1+ defaults to rejecting any single form field over ~500 KB
# before the app even sees the request (413), so this stays comfortably
# under that — otherwise oversized input gets a generic Werkzeug 413 instead
# of this module's clearer 422 message.
MAX_EMAIL_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_EMAIL_EXTENSIONS = {".eml", ".msg"}

# Control characters (other than \t\r\n, which are normal in email source)
# have no legitimate reason to appear in pasted email content.
_ALLOWED_CONTROL_CHARS = {"\t", "\r", "\n"}


def validate_email_text(value: str) -> str:
    value = value.strip()
    if not value:
        raise APIError("Email content is required.", 422)
    if len(value) > MAX_EMAIL_TEXT_LENGTH:
        raise APIError(f"Email content is too long (max {MAX_EMAIL_TEXT_LENGTH} characters).", 422)
    if any((ord(c) < 0x20 or ord(c) == 0x7F) and c not in _ALLOWED_CONTROL_CHARS for c in value):
        raise APIError("Email content must not contain control characters.", 422)
    return value


def validate_email_upload(filename: str, content: bytes) -> str:
    """Returns the validated file extension (e.g. '.eml')."""
    if not filename:
        raise APIError("Uploaded file has no filename.", 422)

    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EMAIL_EXTENSIONS:
        raise APIError(
            f"Unsupported file type '{ext}'. Only {', '.join(sorted(ALLOWED_EMAIL_EXTENSIONS))} are supported.",
            422,
        )

    if not content:
        raise APIError("Uploaded file is empty.", 422)
    if len(content) > MAX_EMAIL_UPLOAD_BYTES:
        raise APIError(f"Uploaded file is too large (max {MAX_EMAIL_UPLOAD_BYTES // (1024 * 1024)} MB).", 422)

    return ext
