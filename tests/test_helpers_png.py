"""Tests for shared PNG test helpers."""

from __future__ import annotations

import pytest

from tests.helpers.png import (
    PNG_SIGNATURE,
    assert_png_structure,
    make_png_bytes,
    png_chunk_names,
    png_text_chunks,
)


def test_assert_png_structure_accepts_generated_png() -> None:
    data = make_png_bytes()

    assert_png_structure(data)
    assert png_chunk_names(data)[:1] == [b"IHDR"]
    assert png_chunk_names(data)[-1:] == [b"IEND"]
    assert png_text_chunks(data)["Comment"] == "metadata makes this fixture less optimized"


def test_assert_png_structure_rejects_bad_signature() -> None:
    with pytest.raises(AssertionError, match="PNG signature"):
        assert_png_structure(b"not a png")


def test_assert_png_structure_rejects_trailing_bytes_after_iend() -> None:
    data = make_png_bytes() + b"trailing"

    with pytest.raises(AssertionError, match="trailing data"):
        assert_png_structure(data)


def test_assert_png_structure_rejects_crc_mismatch() -> None:
    data = bytearray(make_png_bytes())
    data[len(PNG_SIGNATURE) + 8] ^= 0x01

    with pytest.raises(AssertionError, match=r"invalid .* CRC"):
        assert_png_structure(bytes(data))
