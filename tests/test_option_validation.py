"""Cross-entry-point option validation tests."""

import warnings
from typing import Any, cast

import pytest

from oxipng import (
    ColorType,
    Deflaters,
    FilterStrategy,
    PngError,
    RawImage,
    RowFilter,
    StripChunks,
    optimize_from_memory,
)
from tests.helpers.png import assert_png_structure
from tests.helpers.warnings import PYOXIPNG_WARNING


class ExplodingValue:
    @property
    def value(self) -> str:
        raise RuntimeError("value property exploded")


def test_predefined_filter_factory_uses_basic_filters_without_warning() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
            row_filter = RowFilter.none
        predefined = FilterStrategy.predefined([row_filter, "sub", FilterStrategy.up])

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert predefined.filters == ("none", "sub", "up")


def test_predefined_filter_rejects_empty_sequence() -> None:
    with pytest.raises(ValueError, match="predefined filter must not be empty"):
        FilterStrategy.predefined([])


@pytest.mark.parametrize("value", ["minsum", FilterStrategy.entropy, "unknown"])
def test_predefined_filter_rejects_non_basic_filters(value: object) -> None:
    with pytest.raises(ValueError, match="predefined filter"):
        FilterStrategy.predefined([value])


@pytest.mark.parametrize("names", [["abc"], ["abcde"], ["ab1d"]])
def test_strip_factories_reject_invalid_chunk_names(
    png_bytes: bytes,
    names: list[str],
) -> None:
    strip = StripChunks.strip(names)

    with pytest.raises(ValueError, match="chunk name"):
        optimize_from_memory(png_bytes, strip=strip)


def test_strip_factories_accept_iterables(png_bytes: bytes) -> None:
    strip = StripChunks.strip(name for name in ["tEXt"])
    keep = StripChunks.keep(name for name in ["IHDR", "IDAT", "IEND"])

    assert_png_structure(optimize_from_memory(png_bytes, strip=strip))
    assert_png_structure(optimize_from_memory(png_bytes, strip=keep))


def test_predefined_filter_accepts_iterables(png_bytes: bytes) -> None:
    filters = FilterStrategy.predefined(name for name in ["none", "sub"])

    assert_png_structure(optimize_from_memory(png_bytes, filter=filters))


def test_predefined_filter_rejects_mapping() -> None:
    with pytest.raises(TypeError, match="predefined filters must be an iterable"):
        cast("Any", FilterStrategy.predefined)({"none": True})


@pytest.mark.parametrize(
    "names",
    ["tEXt", b"tEXt", bytearray(b"tEXt"), memoryview(b"tEXt"), {"tEXt": True}],
)
def test_strip_factories_reject_scalar_and_mapping_outer_containers(names: object) -> None:
    with pytest.raises(TypeError, match="chunk names must be an iterable"):
        cast("Any", StripChunks.strip)(names)


def test_strip_factories_reject_byte_chunk_names() -> None:
    with pytest.raises(TypeError, match="chunk names must be strings"):
        cast("Any", StripChunks.strip)([b"tEXt"])


@pytest.mark.parametrize(
    "filters",
    ["none", b"none", bytearray(b"none"), memoryview(b"none"), {"none": True}],
)
def test_predefined_filter_rejects_scalar_and_mapping_outer_containers(
    filters: object,
) -> None:
    with pytest.raises(TypeError, match="predefined filters must be an iterable"):
        cast("Any", FilterStrategy.predefined)(filters)


@pytest.mark.parametrize(("factory", "value"), [(Deflaters.libdeflater, 13), (Deflaters.zopfli, 0)])
def test_pyoxipng_deflaters_reject_invalid_values(
    png_bytes: bytes,
    factory: Any,
    value: int,
) -> None:
    deflater = factory(value)

    with pytest.raises(ValueError, match="deflate"):
        optimize_from_memory(png_bytes, deflate=deflater)


@pytest.mark.parametrize(
    ("value", "error_type"),
    [(True, TypeError), (False, TypeError), (-1, ValueError), ("bad", TypeError)],
)
def test_max_decompressed_size_rejects_invalid_values(
    png_bytes: bytes,
    value: object,
    error_type: type[Exception],
) -> None:
    with pytest.raises(error_type, match="max_decompressed_size"):
        cast("Any", optimize_from_memory)(png_bytes, max_decompressed_size=value)


@pytest.mark.parametrize("level", [-1, 7])
def test_optimize_from_memory_level_rejects_out_of_range_values(
    png_bytes: bytes,
    level: int,
) -> None:
    with pytest.raises(ValueError, match="level must be between 0 and 6"):
        optimize_from_memory(png_bytes, level=level)


@pytest.mark.parametrize("value", [-1])
def test_max_decompressed_size_rejects_negative_values(
    png_bytes: bytes,
    value: int,
) -> None:
    with pytest.raises(ValueError, match="max_decompressed_size"):
        optimize_from_memory(png_bytes, max_decompressed_size=value)


def test_max_decompressed_size_zero_is_not_a_validation_error() -> None:
    with pytest.raises(PngError):
        optimize_from_memory(b"", max_decompressed_size=0)


def test_enum_value_property_errors_are_propagated(png_bytes: bytes) -> None:
    with pytest.raises(RuntimeError, match="value property exploded"):
        cast("Any", optimize_from_memory)(png_bytes, filter=ExplodingValue())


def test_bit_depth_value_property_errors_are_propagated() -> None:
    with pytest.raises(RuntimeError, match="value property exploded"):
        cast("Any", RawImage)(1, 1, ColorType.rgb, ExplodingValue(), bytes([255, 0, 0]))
