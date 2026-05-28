"""Shared test fixtures."""

import binascii
import struct
import zlib
from io import BytesIO
from pathlib import Path

import pytest


def _make_png_bytes() -> bytes:
    """Create small PNG bytes that oxipng can optimize."""
    try:
        from PIL import Image, PngImagePlugin  # noqa: PLC0415 - absent in Python 3.10 API matrix.
    except ModuleNotFoundError:
        return _make_stdlib_png_bytes()
    else:
        buffer = BytesIO()
        info = PngImagePlugin.PngInfo()
        info.add_text("Comment", "metadata makes this fixture less optimized")
        image = Image.new("RGBA", (32, 32), (255, 255, 255, 255))
        image.save(buffer, format="PNG", pnginfo=info)
        return buffer.getvalue()


def _png_chunk(name: bytes, data: bytes) -> bytes:
    return (
        len(data).to_bytes(4, "big") + name + data + binascii.crc32(name + data).to_bytes(4, "big")
    )


def _make_stdlib_png_bytes() -> bytes:
    width = 32
    height = 32
    pixel = bytes([255, 255, 255, 255])
    rows = b"".join(b"\x00" + pixel * width for _ in range(height))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"".join(
        (
            b"\x89PNG\r\n\x1a\n",
            _png_chunk(b"IHDR", ihdr),
            _png_chunk(b"tEXt", b"Comment\x00metadata makes this fixture less optimized"),
            _png_chunk(b"IDAT", zlib.compress(rows)),
            _png_chunk(b"IEND", b""),
        )
    )


@pytest.fixture
def png_bytes() -> bytes:
    """Return generated PNG bytes."""
    return _make_png_bytes()


@pytest.fixture
def png_path(tmp_path: Path, png_bytes: bytes) -> Path:
    """Create a small PNG that oxipng can optimize."""
    path = tmp_path / "cover.png"
    path.write_bytes(png_bytes)
    return path


@pytest.fixture
def corrupt_png_path(tmp_path: Path) -> Path:
    """Create a file that is not a PNG."""
    path = tmp_path / "not-a-png.png"
    path.write_bytes(b"not a png")
    return path
