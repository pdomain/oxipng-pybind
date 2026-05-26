"""Behavior tests using real PNG files generated with Pillow."""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

import pytest
from PIL import Image, PngImagePlugin

from oxipng import BitDepth, ColorType, RawImage, optimize, optimize_from_memory

if TYPE_CHECKING:
    from pathlib import Path


def make_real_png(mode: str) -> bytes:  # noqa: PLR0912
    """Create a PNG with real encoder output and non-trivial pixels."""
    info = PngImagePlugin.PngInfo()
    info.add_text("Comment", f"real png corpus {mode}")

    if mode == "RGB":
        image = Image.new("RGB", (8, 8))
        for y in range(8):
            for x in range(8):
                image.putpixel((x, y), (x * 31, y * 29, (x + y) * 13))
    elif mode == "RGBA":
        image = Image.new("RGBA", (8, 8))
        for y in range(8):
            for x in range(8):
                image.putpixel((x, y), (x * 31, y * 29, 128, x * y * 4))
    elif mode == "L":
        image = Image.new("L", (8, 8))
        for y in range(8):
            for x in range(8):
                image.putpixel((x, y), x * 16 + y * 8)
    elif mode == "P":
        image = Image.new("P", (8, 8))
        palette: list[int] = []
        for index in range(256):
            palette.extend((index, 255 - index, (index * 17) % 256))
        image.putpalette(palette)
        for y in range(8):
            for x in range(8):
                image.putpixel((x, y), (x + y * 8) % 16)
    else:
        raise ValueError(f"unsupported mode {mode}")

    buffer = BytesIO()
    image.save(buffer, format="PNG", pnginfo=info)
    return buffer.getvalue()


def decoded_rgba(data: bytes) -> tuple[tuple[int, int], bytes]:
    """Decode PNG bytes to dimensions and RGBA pixels."""
    with Image.open(BytesIO(data)) as image:
        rgba = image.convert("RGBA")
        return rgba.size, rgba.tobytes()


@pytest.mark.parametrize("mode", ["RGB", "RGBA", "L", "P"])
def test_optimize_real_png_file_preserves_pixels(tmp_path: Path, mode: str) -> None:
    original = make_real_png(mode)
    input_path = tmp_path / f"{mode.lower()}.png"
    output_path = tmp_path / f"{mode.lower()}.optimized.png"
    input_path.write_bytes(original)

    optimize(input_path, output_path, level=4, strip="safe")

    assert decoded_rgba(output_path.read_bytes()) == decoded_rgba(original)


@pytest.mark.parametrize("mode", ["RGB", "RGBA", "L", "P"])
def test_optimize_real_png_memory_preserves_pixels(mode: str) -> None:
    original = make_real_png(mode)

    optimized = optimize_from_memory(original, level=4, strip="safe")

    assert decoded_rgba(optimized) == decoded_rgba(original)


def test_raw_image_rgba_preserves_pixels() -> None:
    raw_pixels = bytes(
        [
            255,
            0,
            0,
            255,
            0,
            255,
            0,
            128,
            0,
            0,
            255,
            64,
            255,
            255,
            255,
            0,
        ]
    )
    raw = RawImage(2, 2, ColorType.rgba, BitDepth.eight, raw_pixels)

    optimized = raw.create_optimized_png(level=3)

    assert decoded_rgba(optimized) == (
        (2, 2),
        raw_pixels,
    )
