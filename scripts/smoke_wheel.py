#!/usr/bin/env python3
"""Smoke-test an installed oxipng wheel."""

from __future__ import annotations

import argparse
import binascii
import struct
import zlib
from importlib import metadata, util
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import oxipng
from oxipng import BitDepth, ColorType, PngError, RawImage, optimize, optimize_from_memory

TYPING_FILES = {"oxipng/__init__.pyi", "oxipng/py.typed"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def png_chunk(name: bytes, data: bytes) -> bytes:
    """Return one PNG chunk with CRC."""
    return (
        len(data).to_bytes(4, "big") + name + data + binascii.crc32(name + data).to_bytes(4, "big")
    )


def make_stdlib_png_bytes() -> bytes:
    """Create a small RGBA PNG without external dependencies."""
    width = 16
    height = 16
    pixel = bytes([255, 255, 255, 255])
    rows = b"".join(b"\x00" + pixel * width for _ in range(height))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"".join(
        (
            PNG_SIGNATURE,
            png_chunk(b"IHDR", ihdr),
            png_chunk(b"tEXt", b"Comment\x00wheel smoke metadata"),
            png_chunk(b"IDAT", zlib.compress(rows)),
            png_chunk(b"IEND", b""),
        )
    )


def make_pillow_png_bytes() -> bytes:
    """Create a small PNG for smoke testing."""
    from PIL import Image, PngImagePlugin  # noqa: PLC0415 - optional 3.11+ smoke dependency.

    buffer = BytesIO()
    info = PngImagePlugin.PngInfo()
    info.add_text("Comment", "wheel smoke metadata")
    Image.new("RGBA", (16, 16), (255, 255, 255, 255)).save(buffer, format="PNG", pnginfo=info)
    return buffer.getvalue()


def verify_png_with_pillow(path: Path) -> None:
    """Verify a PNG file with Pillow."""
    from PIL import Image  # noqa: PLC0415 - optional 3.11+ smoke dependency.

    with Image.open(path) as image:
        image.verify()


def verify_png_bytes_with_pillow(data: bytes) -> None:
    """Verify PNG bytes with Pillow."""
    from PIL import Image  # noqa: PLC0415 - optional 3.11+ smoke dependency.

    with Image.open(BytesIO(data)) as image:
        image.verify()


def verify_png_bytes_stdlib(data: bytes) -> None:
    """Verify PNG bytes without external dependencies."""
    if not data.startswith(PNG_SIGNATURE):
        raise RuntimeError("PNG output is missing the PNG signature")
    offset = len(PNG_SIGNATURE)
    chunks: list[bytes] = []
    while offset + 12 <= len(data):
        length = int.from_bytes(data[offset : offset + 4], "big")
        name = data[offset + 4 : offset + 8]
        payload_start = offset + 8
        payload_end = payload_start + length
        crc_end = payload_end + 4
        if crc_end > len(data):
            raise RuntimeError("PNG output has a truncated chunk")
        expected_crc = int.from_bytes(data[payload_end:crc_end], "big")
        actual_crc = binascii.crc32(name + data[payload_start:payload_end])
        if actual_crc != expected_crc:
            raise RuntimeError(f"PNG output has an invalid {name.decode('ascii')} CRC")
        chunks.append(name)
        offset = crc_end
        if name == b"IEND":
            break
    if chunks[:1] != [b"IHDR"] or chunks[-1:] != [b"IEND"] or b"IDAT" not in chunks:
        raise RuntimeError("PNG output is missing required chunks")


def verify_png_stdlib(path: Path) -> None:
    """Verify a PNG file without external dependencies."""
    verify_png_bytes_stdlib(path.read_bytes())


def verify_packaged_typing_files(*, allow_editable: bool = False) -> None:
    """Verify wheel includes typing metadata."""
    files = metadata.files("oxipng-pybind")
    if files is None:
        raise RuntimeError("installed distribution has no file metadata")

    names = {str(path) for path in files}
    missing = TYPING_FILES - names
    if not missing:
        return

    if allow_editable and "oxipng_pybind.pth" in names:
        package_spec = util.find_spec("oxipng")
        locations = package_spec.submodule_search_locations if package_spec else None
        package_root = Path(next(iter(locations))) if locations else None
        if package_root is not None and all(
            (package_root / file_name.removeprefix("oxipng/")).is_file() for file_name in missing
        ):
            return

    raise RuntimeError(f"wheel is missing {', '.join(sorted(missing))}")


def main(argv: list[str] | None = None) -> int:
    """Run smoke checks."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-editable",
        action="store_true",
        help="allow source-tree typing fallback for editable installs",
    )
    parser.add_argument(
        "--stdlib-png",
        action="store_true",
        help="avoid Pillow and use stdlib PNG generation and validation",
    )
    args = parser.parse_args(argv)

    if oxipng.__name__ != "oxipng":
        raise RuntimeError("imported unexpected oxipng module")
    if PngError.__name__ != "PngError":
        raise RuntimeError("imported unexpected PngError type")
    verify_packaged_typing_files(allow_editable=args.allow_editable)
    data = make_stdlib_png_bytes() if args.stdlib_png else make_pillow_png_bytes()
    verify_png = verify_png_stdlib if args.stdlib_png else verify_png_with_pillow
    verify_png_bytes = verify_png_bytes_stdlib if args.stdlib_png else verify_png_bytes_with_pillow

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
