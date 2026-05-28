"""Shared PNG fixtures and assertions for tests."""

from __future__ import annotations

import binascii
import struct
import zlib
from io import BytesIO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def png_chunk(name: bytes, data: bytes) -> bytes:
    return (
        len(data).to_bytes(4, "big") + name + data + binascii.crc32(name + data).to_bytes(4, "big")
    )


def make_png_bytes() -> bytes:
    try:
        from PIL import Image, PngImagePlugin  # noqa: PLC0415 - optional on Python 3.10 lane.
    except ModuleNotFoundError:
        return make_stdlib_png_bytes()

    buffer = BytesIO()
    info = PngImagePlugin.PngInfo()
    info.add_text("Comment", "metadata makes this fixture less optimized")
    image = Image.new("RGBA", (32, 32), (255, 255, 255, 255))
    image.save(buffer, format="PNG", pnginfo=info)
    return buffer.getvalue()


def make_stdlib_png_bytes() -> bytes:
    width = 32
    height = 32
    pixel = bytes([255, 255, 255, 255])
    rows = b"".join(b"\x00" + pixel * width for _ in range(height))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"".join(
        (
            PNG_SIGNATURE,
            png_chunk(b"IHDR", ihdr),
            png_chunk(b"tEXt", b"Comment\x00metadata makes this fixture less optimized"),
            png_chunk(b"IDAT", zlib.compress(rows)),
            png_chunk(b"IEND", b""),
        )
    )


def assert_png_path(path: Path) -> None:
    assert_png_structure(path.read_bytes())


def assert_png_structure(data: bytes) -> None:
    if not data.startswith(PNG_SIGNATURE):
        raise AssertionError("PNG output is missing the PNG signature")

    chunks: list[bytes] = []
    offset = len(PNG_SIGNATURE)
    while offset + 12 <= len(data):
        length = int.from_bytes(data[offset : offset + 4], "big")
        name = data[offset + 4 : offset + 8]
        payload_start = offset + 8
        payload_end = payload_start + length
        crc_end = payload_end + 4
        if crc_end > len(data):
            raise AssertionError("PNG output has a truncated chunk")
        expected_crc = int.from_bytes(data[payload_end:crc_end], "big")
        actual_crc = binascii.crc32(name + data[payload_start:payload_end])
        if actual_crc != expected_crc:
            raise AssertionError(f"PNG output has an invalid {name.decode('ascii')} CRC")
        chunks.append(name)
        offset = crc_end
        if name == b"IEND":
            break

    if chunks[:1] != [b"IHDR"] or chunks[-1:] != [b"IEND"] or b"IDAT" not in chunks:
        raise AssertionError("PNG output is missing required chunks")
    if offset != len(data):
        raise AssertionError("PNG output has trailing data after IEND")


def png_chunk_names(data: bytes) -> list[bytes]:
    assert_png_structure(data)

    chunks: list[bytes] = []
    offset = len(PNG_SIGNATURE)
    while offset + 12 <= len(data):
        length = int.from_bytes(data[offset : offset + 4], "big")
        name = data[offset + 4 : offset + 8]
        chunks.append(name)
        offset += 12 + length
        if name == b"IEND":
            break
    return chunks


def png_text_chunks(data: bytes) -> dict[str, str]:
    assert_png_structure(data)

    chunks: dict[str, str] = {}
    offset = len(PNG_SIGNATURE)
    while offset + 12 <= len(data):
        length = int.from_bytes(data[offset : offset + 4], "big")
        name = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        if name == b"tEXt":
            key, _, value = payload.partition(b"\x00")
            chunks[key.decode("latin-1")] = value.decode("latin-1")
        offset += 12 + length
        if name == b"IEND":
            break
    return chunks


def decoded_rgba(data: bytes) -> tuple[tuple[int, int], bytes]:
    from PIL import Image  # noqa: PLC0415 - real pixel tests require Pillow.

    with Image.open(BytesIO(data)) as image:
        rgba = image.convert("RGBA")
        return rgba.size, rgba.tobytes()


def assert_same_pixels(left: bytes, right: bytes) -> None:
    assert decoded_rgba(right) == decoded_rgba(left)


def write_png(path: Path, data: bytes | None = None) -> Path:
    path.write_bytes(make_png_bytes() if data is None else data)
    return path
