import io

import pytest
import qrcode
from PIL import Image

from app.services.qr_scanner.decoder import InvalidImageError, NoQRCodeFoundError, decode_qr_image


def make_qr_png(content: str) -> bytes:
    img = qrcode.make(content)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_decodes_real_qr_png():
    content = decode_qr_image(make_qr_png("https://example.com"))
    assert content == "https://example.com"


def test_decodes_real_qr_jpeg():
    img = qrcode.make("hello world").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    content = decode_qr_image(buf.getvalue())
    assert content == "hello world"


def test_decodes_real_qr_webp():
    img = qrcode.make("hello webp").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="WEBP")
    content = decode_qr_image(buf.getvalue())
    assert content == "hello webp"


def test_rejects_malformed_image_bytes():
    with pytest.raises(InvalidImageError):
        decode_qr_image(b"this is not an image at all")


def test_rejects_empty_bytes():
    with pytest.raises(InvalidImageError):
        decode_qr_image(b"")


def test_rejects_valid_image_with_no_qr_code():
    blank = Image.new("RGB", (200, 200), color="white")
    buf = io.BytesIO()
    blank.save(buf, format="PNG")
    with pytest.raises(NoQRCodeFoundError):
        decode_qr_image(buf.getvalue())


def test_rejects_unsupported_format():
    img = Image.new("RGB", (50, 50), color="white")
    buf = io.BytesIO()
    img.save(buf, format="BMP")
    with pytest.raises(InvalidImageError):
        decode_qr_image(buf.getvalue())
