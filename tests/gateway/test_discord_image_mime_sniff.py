"""Regression tests for issue #21049.

Discord's reported Content-Type can disagree with the actual image
bytes. Anthropic now validates media_type against magic bytes and
rejects mismatches with HTTP 400. ``_sniff_image_mime`` returns the
canonical MIME for the leading bytes so the gateway can override the
Discord-reported value when it is wrong.
"""

from gateway.platforms.discord import _sniff_image_mime


_PNG_HEAD = b"\x89PNG\r\n\x1a\n" + b"\x00" * 4
_JPEG_HEAD = b"\xff\xd8\xff\xe0" + b"\x00" * 8
_GIF87_HEAD = b"GIF87a" + b"\x00" * 6
_GIF89_HEAD = b"GIF89a" + b"\x00" * 6
_WEBP_HEAD = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP"


def test_sniff_png():
    assert _sniff_image_mime(_PNG_HEAD) == "image/png"


def test_sniff_jpeg():
    assert _sniff_image_mime(_JPEG_HEAD) == "image/jpeg"


def test_sniff_gif87():
    assert _sniff_image_mime(_GIF87_HEAD) == "image/gif"


def test_sniff_gif89():
    assert _sniff_image_mime(_GIF89_HEAD) == "image/gif"


def test_sniff_webp():
    assert _sniff_image_mime(_WEBP_HEAD) == "image/webp"


def test_sniff_unknown_returns_none():
    assert _sniff_image_mime(b"<html>forbidden</html>") is None


def test_sniff_too_short_returns_none_for_webp_check():
    """The WEBP check requires >=12 bytes; shorter input must not crash."""
    assert _sniff_image_mime(b"RIFF") is None


def test_sniff_empty_returns_none():
    assert _sniff_image_mime(b"") is None