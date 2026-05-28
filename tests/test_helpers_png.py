"""Tests for shared PNG test helpers."""

from __future__ import annotations

import pytest

from tests.helpers.png import (
    PNG_SIGNATURE,
    assert_png_structure,
    make_png_bytes,
    png_chunk,
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


def test_assert_png_structure_rejects_invalid_chunk_name() -> None:
    data = make_png_bytes()
    malformed = data[:-12] + png_chunk(b"1234", b"") + data[-12:]

    with pytest.raises(AssertionError, match="invalid chunk name"):
        assert_png_structure(malformed)


def test_png_chunk_names_rejects_crc_mismatch() -> None:
    data = bytearray(make_png_bytes())
    data[len(PNG_SIGNATURE) + 8] ^= 0x01

    with pytest.raises(AssertionError, match=r"invalid .* CRC"):
        png_chunk_names(bytes(data))


def test_png_text_chunks_rejects_malformed_text_without_separator() -> None:
    data = make_png_bytes()
    malformed = data[:-12] + png_chunk(b"tEXt", b"Comment without separator") + data[-12:]

    with pytest.raises(AssertionError, match="malformed tEXt"):
        png_text_chunks(malformed)


def test_png_text_chunks_rejects_trailing_bytes_after_iend() -> None:
    data = make_png_bytes() + b"trailing"

    with pytest.raises(AssertionError, match="trailing data"):
        png_text_chunks(data)
