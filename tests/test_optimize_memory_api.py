"""Memory optimize public API tests."""

import array
from typing import Any, cast

import pytest

from oxipng import (
    Deflater,
    Deflaters,
    FilterStrategy,
    Interlacing,
    PngError,
    RowFilter,
    StripChunks,
    optimize_from_memory,
)
from tests.helpers.png import assert_png_structure
from tests.helpers.warnings import PYOXIPNG_WARNING, assert_no_deprecation_warning


class BytesMethodOnly:
    data: bytes

    def __init__(self, data: bytes) -> None:
        self.data = data

    def tobytes(self) -> bytes:
        return self.data


@pytest.mark.parametrize(
    "value",
    [
        FilterStrategy.none,
        FilterStrategy.sub,
        FilterStrategy.up,
        FilterStrategy.average,
        FilterStrategy.paeth,
        FilterStrategy.minsum,
        FilterStrategy.entropy,
        FilterStrategy.bigrams,
        FilterStrategy.bigent,
        FilterStrategy.brute,
        "none",
        "0",
        "sub",
        "1",
        "up",
        "2",
        "average",
        "3",
        "paeth",
        "4",
        "minsum",
        "5",
        "entropy",
        "6",
        "bigrams",
        "7",
        "bigent",
        "8",
        "brute",
        "9",
    ],
)
def test_filter_enum_and_string_aliases_for_memory(png_bytes: bytes, value: object) -> None:
    output = cast("Any", optimize_from_memory)(png_bytes, filter=value)

    assert_png_structure(output)


def test_filter_sequence_is_accepted(png_bytes: bytes) -> None:
    output = optimize_from_memory(png_bytes, filter=[FilterStrategy.none, "sub", "sub"])

    assert_png_structure(output)


def test_predefined_filter_optimizes_memory(png_bytes: bytes) -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        row_filter = RowFilter.sub
    predefined = FilterStrategy.predefined(["none", row_filter, FilterStrategy.up])

    output = optimize_from_memory(png_bytes, filter=predefined)

    assert_png_structure(output)


def test_pyoxipng_rowfilter_values_optimize_memory(png_bytes: bytes) -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        none = RowFilter.none
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        sub = RowFilter.sub

    output = optimize_from_memory(png_bytes, filter={none, sub})

    assert_png_structure(output)


def test_pyoxipng_strip_member_factories_warn_and_work(png_bytes: bytes) -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        none = StripChunks.none()
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        safe = StripChunks.safe()
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        all_ = StripChunks.all()

    assert none is StripChunks.none
    assert safe is StripChunks.safe
    assert all_ is StripChunks.all
    assert isinstance(none, StripChunks)
    assert isinstance(safe, StripChunks)
    assert isinstance(all_, StripChunks)

    output_none, output_safe, output_all = assert_no_deprecation_warning(
        lambda: (
            optimize_from_memory(png_bytes, strip=none),
            optimize_from_memory(png_bytes, strip=safe),
            optimize_from_memory(png_bytes, strip=all_),
        )
    )
    assert_png_structure(output_none)
    assert_png_structure(output_safe)
    assert_png_structure(output_all)


def test_pyoxipng_deflaters_optimize_memory(png_bytes: bytes) -> None:
    libdeflater, zopfli = assert_no_deprecation_warning(
        lambda: (Deflaters.libdeflater(12), Deflaters.zopfli(1))
    )
    assert_png_structure(optimize_from_memory(png_bytes, deflate=libdeflater))
    assert_png_structure(optimize_from_memory(png_bytes, deflate=zopfli))


@pytest.mark.parametrize(
    "option",
    [
        "optimize_alpha",
        "bit_depth_reduction",
        "color_type_reduction",
        "palette_reduction",
        "grayscale_reduction",
        "idat_recoding",
        "scale_16",
        "fast_evaluation",
    ],
)
def test_advanced_bool_options_optimize_memory_without_warning(
    png_bytes: bytes,
    option: str,
) -> None:
    output = assert_no_deprecation_warning(
        lambda: cast("Any", optimize_from_memory)(png_bytes, **{option: False})
    )
    assert_png_structure(output)


def test_timeout_optimizes_memory_without_warning(png_bytes: bytes) -> None:
    output = assert_no_deprecation_warning(lambda: optimize_from_memory(png_bytes, timeout=1.0))
    assert_png_structure(output)


def test_timeout_none_optimizes_memory_without_warning(png_bytes: bytes) -> None:
    output = assert_no_deprecation_warning(lambda: optimize_from_memory(png_bytes, timeout=None))
    assert_png_structure(output)


def test_advanced_bool_none_optimizes_memory_without_warning(png_bytes: bytes) -> None:
    output = assert_no_deprecation_warning(
        lambda: optimize_from_memory(png_bytes, optimize_alpha=None)
    )
    assert_png_structure(output)


@pytest.mark.parametrize("value", [None, 10_000_000])
def test_max_decompressed_size_optimizes_memory_without_warning(
    png_bytes: bytes,
    value: int | None,
) -> None:
    output = assert_no_deprecation_warning(
        lambda: optimize_from_memory(png_bytes, max_decompressed_size=value)
    )
    assert_png_structure(output)


@pytest.mark.parametrize("value", [float("inf"), 1e300])
def test_pyoxipng_timeout_rejects_out_of_range_values(png_bytes: bytes, value: float) -> None:
    with pytest.raises(ValueError, match="timeout"):
        optimize_from_memory(png_bytes, timeout=value)


@pytest.mark.parametrize("value", [True, False])
def test_pyoxipng_timeout_rejects_bool(png_bytes: bytes, value: bool) -> None:
    with pytest.raises(TypeError, match="timeout"):
        cast("Any", optimize_from_memory)(png_bytes, timeout=value)


@pytest.mark.parametrize("option", ["optimize_alpha", "bit_depth_reduction", "timeout"])
def test_pyoxipng_advanced_options_reject_invalid_values(option: str, png_bytes: bytes) -> None:
    value: object = "bad"

    with pytest.raises((TypeError, ValueError), match=option):
        cast("Any", optimize_from_memory)(png_bytes, **{option: value})


def test_stable_option_paths_do_not_emit_deprecation_warnings(png_bytes: bytes) -> None:
    output = assert_no_deprecation_warning(
        lambda: optimize_from_memory(
            png_bytes,
            level=2,
            interlace=Interlacing.keep,
            strip=StripChunks.none,
            deflate=Deflater.libdeflater,
            filter=FilterStrategy.none,
            fix_errors=False,
            force=False,
        )
    )
    assert_png_structure(output)


@pytest.mark.parametrize("value", [True, False])
def test_optimize_from_memory_level_rejects_bool(png_bytes: bytes, value: bool) -> None:
    with pytest.raises(TypeError, match="level must be an integer"):
        optimize_from_memory(png_bytes, level=value)


def test_non_bool_memory_flags_raise_type_error(png_bytes: bytes) -> None:
    with pytest.raises(TypeError, match="force must be a bool"):
        cast("Any", optimize_from_memory)(png_bytes, force=1)


@pytest.mark.parametrize("buffer_factory", [bytes, bytearray, memoryview])
def test_optimize_from_memory_accepts_supported_buffers(
    png_bytes: bytes,
    buffer_factory: Any,
) -> None:
    output = optimize_from_memory(buffer_factory(png_bytes))

    assert isinstance(output, bytes)
    assert_png_structure(output)


def test_optimize_from_memory_rejects_generic_buffers(png_bytes: bytes) -> None:
    with pytest.raises(TypeError, match="bytes, bytearray, or memoryview"):
        cast("Any", optimize_from_memory)(array.array("B", png_bytes))


def test_optimize_from_memory_rejects_tobytes_only_objects(png_bytes: bytes) -> None:
    with pytest.raises(TypeError, match="bytes, bytearray, or memoryview"):
        cast("Any", optimize_from_memory)(BytesMethodOnly(png_bytes))


@pytest.mark.parametrize("option", ["backup", "preserve_attrs"])
def test_optimize_from_memory_rejects_file_only_options(png_bytes: bytes, option: str) -> None:
    with pytest.raises(TypeError, match=f"unsupported option: {option}"):
        cast("Any", optimize_from_memory)(png_bytes, **{option: True})


def test_max_decompressed_size_limit_is_enforced(png_bytes: bytes) -> None:
    with pytest.raises(PngError):
        optimize_from_memory(png_bytes, max_decompressed_size=1)


def test_corrupt_memory_input_raises_png_error() -> None:
    with pytest.raises(PngError):
        optimize_from_memory(b"not a png")


def test_optimize_from_memory_rejects_negative_timeout(png_bytes: bytes) -> None:
    with pytest.raises(ValueError, match="timeout"):
        optimize_from_memory(png_bytes, timeout=-1)
