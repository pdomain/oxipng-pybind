"""Shared test fixtures."""

from pathlib import Path

import pytest
from PIL import Image, PngImagePlugin


@pytest.fixture
def png_path(tmp_path: Path) -> Path:
    """Create a small PNG that oxipng can optimize."""
    path = tmp_path / "cover.png"
    info = PngImagePlugin.PngInfo()
    info.add_text("Comment", "metadata makes this fixture less optimized")
    image = Image.new("RGBA", (32, 32), (255, 255, 255, 255))
    image.save(path, pnginfo=info)
    return path


@pytest.fixture
def corrupt_png_path(tmp_path: Path) -> Path:
    """Create a file that is not a PNG."""
    path = tmp_path / "not-a-png.png"
    path.write_bytes(b"not a png")
    return path
