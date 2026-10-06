"""Decodes QR codes from uploaded image bytes.

Uses Pillow (image validation/decoding) + pyzbar (a binding over the zbar
C library) for the actual barcode read. Never writes anything to disk —
images are decoded entirely in memory and discarded, matching the same
no-disk-I/O approach used by the email scanner's file uploads.
"""

import io

from PIL import Image, UnidentifiedImageError
from pyzbar.pyzbar import decode as zbar_decode

ALLOWED_IMAGE_FORMATS = {"PNG", "JPEG", "WEBP"}


class InvalidImageError(Exception):
    """Raised for malformed, oversized, or unsupported-format images."""


class NoQRCodeFoundError(Exception):
    """Raised when the image is valid but no QR code could be located in it."""


def _load_validated_image(content: bytes) -> Image.Image:
    try:
        probe = Image.open(io.BytesIO(content))
        probe.verify()  # checks structural integrity without fully decoding
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise InvalidImageError(f"Could not read this file as an image: {exc}") from exc

    if probe.format not in ALLOWED_IMAGE_FORMATS:
        raise InvalidImageError(
            f"Unsupported image format '{probe.format}'. Only PNG, JPEG, and WEBP are supported."
        )

    try:
        # verify() leaves the image unusable for further operations, so the
        # bytes are re-opened for the actual decode. Pillow's built-in
        # Image.MAX_IMAGE_PIXELS guard (~89 megapixels) still applies here,
        # protecting against decompression-bomb-style oversized images.
        image = Image.open(io.BytesIO(content))
        image.load()
    except Image.DecompressionBombError as exc:
        raise InvalidImageError(f"Image is too large to process safely: {exc}") from exc
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise InvalidImageError(f"Could not decode this image: {exc}") from exc

    return image


def decode_qr_image(content: bytes) -> str:
    """Returns the raw text content of the first QR code found in the image."""
    image = _load_validated_image(content)

    try:
        results = zbar_decode(image)
    except Exception as exc:  # pyzbar/zbar can raise a range of native errors
        raise InvalidImageError(f"Could not scan this image for QR codes: {exc}") from exc

    if not results:
        raise NoQRCodeFoundError("No QR code was found in this image.")

    raw_bytes = results[0].data
    return raw_bytes.decode("utf-8", errors="replace")
