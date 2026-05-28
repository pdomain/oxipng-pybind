"""Shared test fixtures."""

from pathlib import Path

import pytest

from tests.helpers.png import make_png_bytes


@pytest.fixture
def png_bytes() -> bytes:
    """Return generated PNG bytes."""
    return make_png_bytes()


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
