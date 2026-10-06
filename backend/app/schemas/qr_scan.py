import os

from app.utils.errors import APIError

MAX_QR_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_QR_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def validate_qr_upload(filename: str, content: bytes) -> None:
    if not filename:
        raise APIError("Uploaded file has no filename.", 422)

    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_QR_EXTENSIONS:
        raise APIError(
            f"Unsupported file type '{ext}'. Only PNG, JPEG, and WEBP images are supported.",
            422,
        )

    if not content:
        raise APIError("Uploaded file is empty.", 422)
    if len(content) > MAX_QR_UPLOAD_BYTES:
        raise APIError(f"Uploaded file is too large (max {MAX_QR_UPLOAD_BYTES // (1024 * 1024)} MB).", 422)
