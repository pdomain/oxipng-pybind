"""Shared test fixtures."""

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image, PngImagePlugin


def _make_png_bytes() -> bytes:
    """Create small PNG bytes that oxipng can optimize."""
    buffer = BytesIO()
    info = PngImagePlugin.PngInfo()
    info.add_text("Comment", "metadata makes this fixture less optimized")
    image = Image.new("RGBA", (32, 32), (255, 255, 255, 255))
    image.save(buffer, format="PNG", pnginfo=info)
    return buffer.getvalue()


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
