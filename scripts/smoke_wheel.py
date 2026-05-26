#!/usr/bin/env python3
"""Smoke-test an installed oxipng wheel."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, PngImagePlugin

import oxipng
from oxipng import PngError, optimize, optimize_from_memory


def make_png_bytes() -> bytes:
    """Create a small PNG for smoke testing."""
    buffer = BytesIO()
    info = PngImagePlugin.PngInfo()
    info.add_text("Comment", "wheel smoke metadata")
    Image.new("RGBA", (16, 16), (255, 255, 255, 255)).save(buffer, format="PNG", pnginfo=info)
    return buffer.getvalue()


def verify_png(path: Path) -> None:
    """Verify a PNG file with Pillow."""
    with Image.open(path) as image:
        image.verify()


def verify_png_bytes(data: bytes) -> None:
    """Verify PNG bytes with Pillow."""
    with Image.open(BytesIO(data)) as image:
        image.verify()


def main() -> int:
    """Run smoke checks."""
    if oxipng.__name__ != "oxipng":
        raise RuntimeError("imported unexpected oxipng module")
    if PngError.__name__ != "PngError":
        raise RuntimeError("imported unexpected PngError type")
    data = make_png_bytes()

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        in_place = root / "in-place.png"
        output_input = root / "input.png"
        output = root / "output.png"
        in_place.write_bytes(data)
        output_input.write_bytes(data)

        optimize(in_place, strip="safe")
        optimize(output_input, output, filter="none")
        memory_output = optimize_from_memory(data, level=2)

        verify_png(in_place)
        verify_png(output)
        verify_png_bytes(memory_output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
