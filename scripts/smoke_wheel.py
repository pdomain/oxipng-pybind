#!/usr/bin/env python3
"""Smoke-test an installed oxipng wheel."""

from __future__ import annotations

from importlib import metadata, util
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, PngImagePlugin

import oxipng
from oxipng import BitDepth, ColorType, PngError, RawImage, optimize, optimize_from_memory

TYPING_FILES = {"oxipng/__init__.pyi", "oxipng/py.typed"}


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


def verify_packaged_typing_files() -> None:
    """Verify wheel includes typing metadata."""
    files = metadata.files("oxipng-pybind")
    if files is None:
        raise RuntimeError("installed distribution has no file metadata")

    names = {str(path) for path in files}
    missing = TYPING_FILES - names
    if not missing:
        return

    if "oxipng_pybind.pth" in names:
        package_spec = util.find_spec("oxipng")
        locations = package_spec.submodule_search_locations if package_spec else None
        package_root = Path(next(iter(locations))) if locations else None
        if package_root is not None and all(
            (package_root / file_name.removeprefix("oxipng/")).is_file() for file_name in missing
        ):
            return

    raise RuntimeError(f"wheel is missing {', '.join(sorted(missing))}")


def main() -> int:
    """Run smoke checks."""
    if oxipng.__name__ != "oxipng":
        raise RuntimeError("imported unexpected oxipng module")
    if PngError.__name__ != "PngError":
        raise RuntimeError("imported unexpected PngError type")
    verify_packaged_typing_files()
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
        memory_output = optimize_from_memory(bytearray(data), level=2)
        view_output = optimize_from_memory(memoryview(data), level=2)
        raw = RawImage(
            1,
            1,
            ColorType.rgba,
            BitDepth.eight,
            bytes([255, 0, 0, 255]),
        )
        raw.add_png_chunk(b"tEXt", b"Comment\x00wheel smoke raw chunk")
        raw_output = raw.create_optimized_png()

        verify_png(in_place)
        verify_png(output)
        verify_png_bytes(memory_output)
        verify_png_bytes(view_output)
        verify_png_bytes(raw_output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
