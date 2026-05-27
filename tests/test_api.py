"""Supported public API tests."""

import array
import inspect
import os
import warnings
from io import BytesIO
from pathlib import Path
from typing import Any, TypeAlias, cast

import pytest
from PIL import Image

from oxipng import (
    BitDepth,
    ColorType,
    Deflater,
    Deflaters,
    FilterStrategy,
    Interlacing,
    OptimizationResult,
    PngError,
    RawImage,
    RowFilter,
    StripChunks,
    analyze,
    optimize,
    optimize_from_memory,
)

Palette: TypeAlias = list[tuple[int, int, int] | tuple[int, int, int, int]]
PYOXIPNG_WARNING = (
    "pyoxipng compatibility path is unsupported; migrate to oxipng-pybind's stable API; "
    "this compatibility path will be removed in a future release."
)


class CustomPathLike:
    path: Path

    def __init__(self, path: Path) -> None:
        self.path = path

    def __fspath__(self) -> str:
        return str(self.path)


class ExplodingValue:
    @property
    def value(self) -> str:
        raise RuntimeError("value property exploded")


class BytesMethodOnly:
    data: bytes

    def __init__(self, data: bytes) -> None:
        self.data = data

    def tobytes(self) -> bytes:
        return self.data


def assert_readable_png_path(path: Path) -> None:
    """Assert that Pillow can read the optimized PNG."""
    with Image.open(path) as image:
        image.verify()


def assert_readable_png_bytes(data: bytes) -> None:
    """Assert that Pillow can read optimized PNG bytes."""
    with Image.open(BytesIO(data)) as image:
        image.verify()


def png_chunk_names(data: bytes) -> list[bytes]:
    """Return chunk names from PNG bytes."""
    chunks: list[bytes] = []
    offset = 8
    while offset < len(data):
        length = int.from_bytes(data[offset : offset + 4], "big")
        name = data[offset + 4 : offset + 8]
        chunks.append(name)
        offset += 12 + length
        if name == b"IEND":
            break
    return chunks


def test_import_supported_api() -> None:
    assert callable(analyze)
    assert callable(optimize)
    assert callable(optimize_from_memory)
    assert OptimizationResult.__name__ == "OptimizationResult"
    assert issubclass(PngError, Exception)
    assert Interlacing.keep.value == "keep"
    assert StripChunks.safe.value == "safe"
    assert Deflater.libdeflater.value == "libdeflater"
    assert FilterStrategy.brute.value == "brute"
    assert ColorType.rgba.value == "rgba"
    assert BitDepth.eight.value == 8
    assert RawImage.__name__ == "RawImage"


def test_optimize_signature_matches_supported_api() -> None:
    assert str(inspect.signature(optimize)) == (
        "(input, output=None, *, level=2, interlace=None, strip=None, deflate=None, "
        "filter=None, fix_errors=False, force=False, backup=False, preserve_attrs=False, "
        "optimize_alpha=None, bit_depth_reduction=None, color_type_reduction=None, "
        "palette_reduction=None, grayscale_reduction=None, idat_recoding=None, scale_16=None, "
        "fast_evaluation=None, timeout=None, max_decompressed_size=None)"
    )


def test_optimize_from_memory_signature_matches_supported_api() -> None:
    assert str(inspect.signature(optimize_from_memory)) == (
        "(data, *, level=2, interlace=None, strip=None, deflate=None, filter=None, "
        "fix_errors=False, force=False, optimize_alpha=None, bit_depth_reduction=None, "
        "color_type_reduction=None, palette_reduction=None, grayscale_reduction=None, "
        "idat_recoding=None, scale_16=None, fast_evaluation=None, timeout=None, "
        "max_decompressed_size=None)"
    )


def test_analyze_signature_matches_supported_api() -> None:
    assert str(inspect.signature(analyze)) == (
        "(input, *, level=2, interlace=None, strip=None, deflate=None, filter=None, "
        "fix_errors=False, force=False, optimize_alpha=None, bit_depth_reduction=None, "
        "color_type_reduction=None, palette_reduction=None, grayscale_reduction=None, "
        "idat_recoding=None, scale_16=None, fast_evaluation=None, timeout=None, "
        "max_decompressed_size=None)"
    )


def test_public_callables_expose_runtime_docstrings() -> None:
    assert analyze.__doc__ == "Return PNG optimization sizes without writing output."
    assert optimize.__doc__ == "Optimize a PNG file on disk."
    assert optimize_from_memory.__doc__ == "Optimize PNG bytes in memory."
    assert RawImage.__doc__ == "Raw image data for creating optimized PNG bytes."
    assert RawImage.add_png_chunk.__doc__ == "Add an auxiliary PNG chunk."
    assert RawImage.add_icc_profile.__doc__ == "Add an ICC profile."
    assert RawImage.create_optimized_png.__doc__ == "Return optimized PNG bytes."


def test_pyoxipng_compatibility_exports_and_docstrings() -> None:
    assert callable(Deflaters.libdeflater)
    assert callable(Deflaters.zopfli)
    assert callable(StripChunks.strip)
    assert callable(StripChunks.keep)
    assert ColorType.rgb.__call__.__doc__ == (
        "Create a pyoxipng-compatible color descriptor; emits DeprecationWarning."
    )
    assert StripChunks.strip.__doc__ == "Create a strip-chunk option for explicit PNG chunk names."
    assert StripChunks.keep.__doc__ == "Create a keep-chunk option for explicit PNG chunk names."
    assert Deflaters.libdeflater.__doc__ == (
        "Create a libdeflater option with an explicit compression level."
    )
    assert Deflaters.zopfli.__doc__ == "Create a zopfli option with an explicit iteration count."


def test_deprecated_enum_aliases_warn_on_access() -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        off = Interlacing.Off
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        adam7 = Interlacing.Adam7
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        none = RowFilter.none
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        brute = RowFilter.brute

    assert off.value == "off"
    assert adam7.value == "on"
    assert none.value == "none"
    assert brute.value == "brute"


def test_stable_enum_members_do_not_warn_on_access() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        interlace = Interlacing.off
        filter_strategy = FilterStrategy.none
        color_type = ColorType.rgba
        bit_depth = BitDepth.eight

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert interlace.value == "off"
    assert filter_strategy.value == "none"
    assert color_type.value == "rgba"
    assert bit_depth.value == 8


def test_pyoxipng_color_factories_warn_and_stable_factories_do_not_warn() -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        color_type = ColorType.rgb(None)
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        rgba = ColorType.rgba()
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        indexed = ColorType.indexed([(255, 0, 0)])
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        grayscale = ColorType.grayscale(None)
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        grayscale_alpha = ColorType.grayscale_alpha()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        strip = StripChunks.strip(["tEXt"])
        keep = StripChunks.keep({"iCCP"})
        libdeflater = Deflaters.libdeflater(12)
        zopfli = Deflaters.zopfli(15)

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert color_type.kind == "rgb"
    assert rgba.kind == "rgba"
    assert indexed.kind == "indexed"
    assert grayscale.kind == "grayscale"
    assert grayscale_alpha.kind == "grayscale_alpha"
    assert strip.mode == "strip"
    assert keep.mode == "keep"
    assert libdeflater.kind == "libdeflater"
    assert zopfli.kind == "zopfli"


def test_pyoxipng_predefined_filter_rejects_non_string_entries() -> None:
    with pytest.raises(TypeError, match="row filter names"):
        FilterStrategy.predefined([object()])


def test_pyoxipng_indexed_color_requires_palette() -> None:
    with (
        pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING),
        pytest.raises(ValueError, match="requires a palette"),
    ):
        ColorType.indexed(None)


@pytest.mark.parametrize("color_type", [ColorType.rgba, ColorType.grayscale_alpha])
def test_pyoxipng_alpha_color_rejects_transparent(color_type: ColorType) -> None:
    with (
        pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING),
        pytest.raises(ValueError, match="does not accept transparent"),
    ):
        color_type(0)


@pytest.mark.parametrize("color_type", [ColorType.rgb, ColorType.grayscale])
def test_pyoxipng_non_indexed_color_rejects_palette(color_type: ColorType) -> None:
    with (
        pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING),
        pytest.raises(TypeError, match="does not accept palette"),
    ):
        color_type([(255, 0, 0)])


def test_optimize_in_place_with_high_compression_level(png_path: Path) -> None:
    optimize(png_path, level=6)

    assert_readable_png_path(png_path)


def test_optimize_to_output_path(png_path: Path, tmp_path: Path) -> None:
    output = tmp_path / "optimized.png"
    optimize(png_path, output, level=6)

    assert output.exists()
    assert_readable_png_path(output)
    assert_readable_png_path(png_path)


def test_analyze_returns_optimization_result_without_writing(png_path: Path) -> None:
    original = png_path.read_bytes()

    result = analyze(png_path)

    assert isinstance(result, OptimizationResult)
    assert isinstance(result.original_size, int)
    assert isinstance(result.optimized_size, int)
    assert result.original_size > 0
    assert result.optimized_size > 0
    assert png_path.read_bytes() == original


def test_analyze_accepts_stable_options_without_warning(png_path: Path) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = analyze(
            png_path,
            level=1,
            strip=StripChunks.safe,
            filter=FilterStrategy.predefined(["none", "sub"]),
            max_decompressed_size=10_000_000,
        )

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert result.original_size > 0
    assert result.optimized_size > 0


@pytest.mark.parametrize("option", ["backup", "preserve_attrs"])
def test_analyze_rejects_file_write_options(png_path: Path, option: str) -> None:
    with pytest.raises(TypeError, match=f"unsupported option: {option}"):
        cast("Any", analyze)(png_path, **{option: True})


def test_optimize_accepts_string_paths(png_path: Path, tmp_path: Path) -> None:
    output = tmp_path / "out.png"

    optimize(str(png_path), str(output))

    assert_readable_png_path(output)


def test_optimize_accepts_custom_pathlike(png_path: Path, tmp_path: Path) -> None:
    output = tmp_path / "out.png"

    optimize(CustomPathLike(png_path), CustomPathLike(output))

    assert_readable_png_path(output)


def test_optimize_interlace_keep_is_accepted(png_path: Path) -> None:
    optimize(png_path, interlace=Interlacing.keep)

    assert_readable_png_path(png_path)


@pytest.mark.parametrize(
    ("option", "value"),
    [
        ("interlace", Interlacing.keep),
        ("interlace", Interlacing.off),
        ("interlace", Interlacing.on),
        ("interlace", "keep"),
        ("interlace", "off"),
        ("interlace", "on"),
        ("interlace", "0"),
        ("interlace", "1"),
        ("strip", StripChunks.none),
        ("strip", StripChunks.safe),
        ("strip", StripChunks.all),
        ("strip", "none"),
        ("strip", "safe"),
        ("strip", "all"),
        ("deflate", Deflater.libdeflater),
        ("deflate", Deflater.zopfli),
        ("deflate", "libdeflater"),
        ("deflate", "zopfli"),
    ],
)
def test_enum_and_string_aliases_for_file_options(
    png_path: Path, option: str, value: object
) -> None:
    cast("Any", optimize)(png_path, **{option: value})

    assert_readable_png_path(png_path)


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

    assert_readable_png_bytes(output)


def test_filter_sequence_is_accepted(png_bytes: bytes) -> None:
    output = optimize_from_memory(png_bytes, filter=[FilterStrategy.none, "sub", "sub"])

    assert_readable_png_bytes(output)


def test_predefined_filter_factory_uses_basic_filters_without_warning() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
            row_filter = RowFilter.none
        predefined = FilterStrategy.predefined([row_filter, "sub", FilterStrategy.up])

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert predefined.filters == ("none", "sub", "up")


def test_predefined_filter_optimizes_memory(png_bytes: bytes) -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        row_filter = RowFilter.sub
    predefined = FilterStrategy.predefined(["none", row_filter, FilterStrategy.up])

    output = optimize_from_memory(png_bytes, filter=predefined)

    assert_readable_png_bytes(output)


def test_predefined_filter_rejects_empty_sequence() -> None:
    with pytest.raises(ValueError, match="predefined filter must not be empty"):
        FilterStrategy.predefined([])


@pytest.mark.parametrize("value", ["minsum", FilterStrategy.entropy, "unknown"])
def test_predefined_filter_rejects_non_basic_filters(value: object) -> None:
    with pytest.raises(ValueError, match="predefined filter"):
        FilterStrategy.predefined([value])


def test_pyoxipng_rowfilter_values_optimize_memory(png_bytes: bytes) -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        none = RowFilter.none
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        sub = RowFilter.sub

    output = optimize_from_memory(png_bytes, filter={none, sub})

    assert_readable_png_bytes(output)


def test_pyoxipng_strip_factories_optimize_file(png_path: Path) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        strip = StripChunks.strip(["tEXt"])

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    optimize(png_path, strip=strip)

    assert_readable_png_path(png_path)


def test_pyoxipng_keep_factories_optimize_file(png_path: Path) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        keep = StripChunks.keep({"iCCP"})

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    optimize(png_path, strip=keep)

    assert_readable_png_path(png_path)


def test_pyoxipng_deflaters_optimize_memory(png_bytes: bytes) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        libdeflater = Deflaters.libdeflater(12)
        zopfli = Deflaters.zopfli(1)

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert_readable_png_bytes(optimize_from_memory(png_bytes, deflate=libdeflater))
    assert_readable_png_bytes(optimize_from_memory(png_bytes, deflate=zopfli))


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
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        output = cast("Any", optimize_from_memory)(png_bytes, **{option: False})

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert_readable_png_bytes(output)


def test_timeout_optimizes_memory_without_warning(png_bytes: bytes) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        output = optimize_from_memory(png_bytes, timeout=1.0)

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert_readable_png_bytes(output)


def test_timeout_none_optimizes_memory_without_warning(png_bytes: bytes) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        output = optimize_from_memory(png_bytes, timeout=None)

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert_readable_png_bytes(output)


def test_advanced_bool_none_optimizes_memory_without_warning(png_bytes: bytes) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        output = optimize_from_memory(png_bytes, optimize_alpha=None)

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert_readable_png_bytes(output)


@pytest.mark.parametrize("value", [None, 10_000_000])
def test_max_decompressed_size_optimizes_memory_without_warning(
    png_bytes: bytes,
    value: int | None,
) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        output = optimize_from_memory(png_bytes, max_decompressed_size=value)

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert_readable_png_bytes(output)


def test_max_decompressed_size_optimizes_file_without_warning(png_path: Path) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        optimize(png_path, max_decompressed_size=10_000_000)

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert_readable_png_path(png_path)


def test_max_decompressed_size_optimizes_raw_image_without_warning() -> None:
    raw = RawImage(1, 1, ColorType.rgba, BitDepth.eight, bytes([255, 0, 0, 255]))

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        output = raw.create_optimized_png(max_decompressed_size=10_000_000)

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert_readable_png_bytes(output)


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
def test_analyze_advanced_bool_options_without_warning(png_path: Path, option: str) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = cast("Any", analyze)(png_path, **{option: False})

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert result.original_size > 0
    assert result.optimized_size > 0


def test_analyze_timeout_without_warning(png_path: Path) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = analyze(png_path, timeout=1.0)

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert result.original_size > 0
    assert result.optimized_size > 0


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
def test_raw_image_advanced_bool_options_without_warning(option: str) -> None:
    raw = RawImage(1, 1, ColorType.rgba, BitDepth.eight, bytes([255, 0, 0, 255]))

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        output = cast("Any", raw.create_optimized_png)(**{option: False})

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert_readable_png_bytes(output)


def test_raw_image_timeout_without_warning() -> None:
    raw = RawImage(1, 1, ColorType.rgba, BitDepth.eight, bytes([255, 0, 0, 255]))

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        output = raw.create_optimized_png(timeout=1.0)

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert_readable_png_bytes(output)


@pytest.mark.parametrize(
    ("value", "error_type"),
    [(True, TypeError), (-1, ValueError), ("bad", TypeError)],
)
def test_max_decompressed_size_rejects_invalid_values(
    png_bytes: bytes,
    value: object,
    error_type: type[Exception],
) -> None:
    with pytest.raises(error_type, match="max_decompressed_size"):
        cast("Any", optimize_from_memory)(png_bytes, max_decompressed_size=value)


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
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        output = optimize_from_memory(
            png_bytes,
            level=2,
            interlace=Interlacing.keep,
            strip=StripChunks.none,
            deflate=Deflater.libdeflater,
            filter=FilterStrategy.none,
            fix_errors=False,
            force=False,
        )

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert_readable_png_bytes(output)


@pytest.mark.parametrize("names", [["abc"], ["abcde"], ["ab1d"]])
def test_pyoxipng_strip_factories_reject_invalid_chunk_names(
    png_bytes: bytes,
    names: list[str],
) -> None:
    strip = StripChunks.strip(names)

    with pytest.raises(ValueError, match="chunk name"):
        optimize_from_memory(png_bytes, strip=strip)


@pytest.mark.parametrize(("factory", "value"), [(Deflaters.libdeflater, 13), (Deflaters.zopfli, 0)])
def test_pyoxipng_deflaters_reject_invalid_values(
    png_bytes: bytes,
    factory: Any,
    value: int,
) -> None:
    deflater = factory(value)

    with pytest.raises(ValueError, match="deflate"):
        optimize_from_memory(png_bytes, deflate=deflater)


@pytest.mark.parametrize("level", [-1, 7])
def test_invalid_level_raises_value_error(png_path: Path, level: int) -> None:
    with pytest.raises(ValueError, match="level must be between 0 and 6"):
        optimize(png_path, level=level)


def test_unsupported_keyword_raises_type_error(png_path: Path) -> None:
    with pytest.raises(TypeError, match="unsupported option: bogus"):
        cast("Any", optimize)(png_path, bogus=True)


@pytest.mark.parametrize(
    ("option", "value"),
    [
        ("interlace", "bad"),
        ("strip", "bad"),
        ("deflate", "bad"),
        ("filter", "bad"),
    ],
)
def test_invalid_enum_string_raises_value_error(png_path: Path, option: str, value: object) -> None:
    with pytest.raises(ValueError, match=option):
        cast("Any", optimize)(png_path, **{option: value})


def test_empty_filter_sequence_raises_value_error(png_path: Path) -> None:
    with pytest.raises(ValueError, match="filter must not be empty"):
        optimize(png_path, filter=[])


@pytest.mark.parametrize("option", ["fix_errors", "force", "backup", "preserve_attrs"])
def test_non_bool_file_flags_raise_type_error(png_path: Path, option: str) -> None:
    with pytest.raises(TypeError, match=f"{option} must be a bool"):
        cast("Any", optimize)(png_path, **{option: 1})


def test_non_bool_memory_flags_raise_type_error(png_bytes: bytes) -> None:
    with pytest.raises(TypeError, match="force must be a bool"):
        cast("Any", optimize_from_memory)(png_bytes, force=1)


def test_backup_with_explicit_output_raises_value_error(png_path: Path, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="backup=True requires in-place optimization"):
        optimize(png_path, tmp_path / "out.png", backup=True)


def test_backup_refuses_to_overwrite_existing_backup(png_path: Path) -> None:
    png_path.with_name(f"{png_path.name}.bak").write_bytes(b"existing backup")

    with pytest.raises(FileExistsError):
        optimize(png_path, backup=True)


@pytest.mark.skipif(not hasattr(__import__("os"), "symlink"), reason="symlink unavailable")
def test_backup_refuses_existing_symlink_backup(png_path: Path, tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    target.write_text("do not overwrite", encoding="utf-8")
    backup = png_path.with_name(f"{png_path.name}.bak")
    backup.symlink_to(target)

    with pytest.raises(FileExistsError):
        optimize(png_path, backup=True)

    assert target.read_text(encoding="utf-8") == "do not overwrite"


def test_backup_creates_copy_for_in_place_optimization(png_path: Path) -> None:
    original = png_path.read_bytes()

    optimize(png_path, backup=True, force=True)

    assert png_path.with_name(f"{png_path.name}.bak").read_bytes() == original
    assert_readable_png_path(png_path)


def test_missing_input_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        optimize(tmp_path / "missing.png")


def test_missing_output_parent_raises_os_error(png_path: Path, tmp_path: Path) -> None:
    with pytest.raises(OSError, match="No such file or directory"):
        optimize(png_path, tmp_path / "missing" / "out.png")


def test_preserve_attrs_copies_permissions_and_mtime(png_path: Path, tmp_path: Path) -> None:
    output = tmp_path / "out.png"
    expected_mtime = 1_700_000_000
    png_path.chmod(0o640)
    os.utime(png_path, (expected_mtime, expected_mtime))

    optimize(png_path, output, preserve_attrs=True)

    assert output.stat().st_mode & 0o777 == 0o640
    assert int(output.stat().st_mtime) == expected_mtime
    assert_readable_png_path(output)


def test_corrupt_input_raises_png_error(corrupt_png_path: Path) -> None:
    with pytest.raises(PngError):
        optimize(corrupt_png_path, level=6)


def test_optimize_from_memory_bytes_returns_readable_bytes(png_bytes: bytes) -> None:
    output = optimize_from_memory(png_bytes)

    assert isinstance(output, bytes)
    assert_readable_png_bytes(output)


def test_optimize_from_memory_bytearray_returns_readable_bytes(png_bytes: bytes) -> None:
    output = optimize_from_memory(bytearray(png_bytes))

    assert_readable_png_bytes(output)


def test_optimize_from_memory_memoryview_returns_readable_bytes(png_bytes: bytes) -> None:
    output = optimize_from_memory(memoryview(png_bytes))

    assert_readable_png_bytes(output)


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


def test_pyoxipng_raw_image_constructor_accepts_rgb_descriptor() -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        color_type = ColorType.rgb(None)
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        raw = RawImage(bytes([255, 0, 0]), 1, 1, color_type=color_type)

    output = raw.create_optimized_png()

    assert_readable_png_bytes(output)


def test_pyoxipng_raw_image_constructor_accepts_rgba_descriptor() -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        color_type = ColorType.rgba()
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        raw = RawImage(bytes([255, 0, 0, 255]), 1, 1, color_type=color_type)

    assert_readable_png_bytes(raw.create_optimized_png())


def test_pyoxipng_raw_image_constructor_accepts_indexed_descriptor() -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        color_type = ColorType.indexed([(255, 0, 0)])
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        raw = RawImage(bytes([0]), 1, 1, color_type=color_type)

    assert_readable_png_bytes(raw.create_optimized_png())


def test_pyoxipng_raw_image_constructor_requires_compat_color_type() -> None:
    with (
        pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING),
        pytest.raises(TypeError, match="color_type"),
    ):
        cast("Any", RawImage)(bytes([255, 0, 0]), 1, 1, color_type="rgb")


def test_stable_raw_image_constructor_does_not_warn() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        raw = RawImage(1, 1, ColorType.rgb, BitDepth.eight, bytes([255, 0, 0]))

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert_readable_png_bytes(raw.create_optimized_png())


def test_stable_raw_image_constructor_accepts_keyword_arguments_without_warning() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        raw = RawImage(
            width=1,
            height=1,
            color_type=ColorType.rgb,
            bit_depth=BitDepth.eight,
            data=bytes([255, 0, 0]),
        )

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert_readable_png_bytes(raw.create_optimized_png())


def test_raw_image_rgba_create_optimized_png_returns_readable_bytes() -> None:
    raw = RawImage(
        2,
        2,
        ColorType.rgba,
        BitDepth.eight,
        bytes(
            [
                255,
                0,
                0,
                255,
                0,
                255,
                0,
                255,
                0,
                0,
                255,
                255,
                255,
                255,
                255,
                255,
            ]
        ),
    )

    output = raw.create_optimized_png(strip=StripChunks.safe)

    assert_readable_png_bytes(output)


def test_raw_image_accepts_string_color_type_and_integer_bit_depth() -> None:
    raw = RawImage(1, 1, "rgb", 8, bytes([255, 0, 0]))

    output = raw.create_optimized_png(level=1)

    assert_readable_png_bytes(output)


def test_raw_image_indexed_palette_returns_readable_bytes() -> None:
    raw = RawImage(
        2,
        1,
        ColorType.indexed,
        BitDepth.eight,
        bytes([0, 1]),
        palette=[(255, 0, 0), (0, 0, 255, 128)],
    )

    output = raw.create_optimized_png()

    assert_readable_png_bytes(output)


def test_raw_image_add_png_chunk_preserves_allowed_chunk() -> None:
    raw = RawImage(1, 1, ColorType.rgb, BitDepth.eight, bytes([255, 0, 0]))
    raw.add_png_chunk(b"tEXt", b"Comment\x00hello")

    output = raw.create_optimized_png(strip=StripChunks.none)

    with Image.open(BytesIO(output)) as image:
        assert cast("Any", image).text["Comment"] == "hello"


def test_raw_image_add_icc_profile_writes_iccp_chunk() -> None:
    raw = RawImage(1, 1, ColorType.rgb, BitDepth.eight, bytes([255, 0, 0]))
    raw.add_icc_profile(b"not a real profile but stored as bytes")

    output = raw.create_optimized_png(strip=StripChunks.none)

    assert b"iCCP" in png_chunk_names(output)
    assert_readable_png_bytes(output)


@pytest.mark.parametrize("name", [b"IHDR", b"IDAT", b"IEND", b"PLTE", b"tRNS", b"iCCP"])
def test_raw_image_rejects_structural_or_dedicated_chunks(name: bytes) -> None:
    raw = RawImage(1, 1, ColorType.rgba, BitDepth.eight, bytes([255, 0, 0, 255]))

    with pytest.raises(ValueError, match="chunk name"):
        raw.add_png_chunk(name, b"payload")


@pytest.mark.parametrize("name", [b"abc", b"abcde", b"ab1d", b"ab_d", b"ab\x00d", b"abCd", b"tEXE"])
def test_raw_image_rejects_invalid_chunk_names(name: bytes) -> None:
    raw = RawImage(1, 1, ColorType.rgba, BitDepth.eight, bytes([255, 0, 0, 255]))

    with pytest.raises(ValueError, match="chunk name"):
        raw.add_png_chunk(name, b"payload")


def test_raw_image_rejects_too_many_palette_entries_for_bit_depth() -> None:
    palette: Palette = [(index, index, index) for index in range(5)]

    with pytest.raises(ValueError, match="palette length"):
        RawImage(1, 1, ColorType.indexed, BitDepth.two, bytes([0]), palette=palette)


def test_raw_image_rejects_indexed_pixels_outside_palette() -> None:
    with pytest.raises(ValueError, match="pixel index"):
        RawImage(
            2,
            1,
            ColorType.indexed,
            BitDepth.eight,
            bytes([0, 2]),
            palette=[(255, 0, 0), (0, 0, 255)],
        )


@pytest.mark.parametrize(
    ("bit_depth", "data"),
    [
        (BitDepth.one, bytes([0b0001_1111])),
        (BitDepth.two, bytes([0b0011_1111])),
        (BitDepth.four, bytes([0x0F])),
    ],
)
def test_raw_image_indexed_ignores_nonzero_padding_bits(bit_depth: BitDepth, data: bytes) -> None:
    raw = RawImage(
        1,
        1,
        ColorType.indexed,
        bit_depth,
        data,
        palette=[(255, 0, 0)],
    )

    output = raw.create_optimized_png()

    assert_readable_png_bytes(output)


def test_raw_image_rejects_sub_byte_indexed_real_pixel_outside_palette() -> None:
    with pytest.raises(ValueError, match="pixel index"):
        RawImage(
            2,
            1,
            ColorType.indexed,
            BitDepth.two,
            bytes([0b0001_0000]),
            palette=[(255, 0, 0)],
        )


def test_raw_image_rejects_grayscale_transparency_above_bit_depth_range() -> None:
    with pytest.raises(ValueError, match="transparent"):
        RawImage(1, 1, ColorType.grayscale, BitDepth.eight, bytes([0]), transparent=256)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"width": True}, "width"),
        ({"height": True}, "height"),
        ({"bit_depth": True}, "bit_depth"),
    ],
)
def test_raw_image_rejects_bool_numeric_shape_values(
    kwargs: dict[str, object], message: str
) -> None:
    arguments: dict[str, object] = {
        "width": 1,
        "height": 1,
        "color_type": ColorType.rgb,
        "bit_depth": BitDepth.eight,
        "data": bytes([255, 0, 0]),
    }
    arguments.update(kwargs)

    with pytest.raises(TypeError, match=message):
        cast("Any", RawImage)(**arguments)


def test_raw_image_rejects_bool_palette_samples() -> None:
    palette = [(True, 0, 0)]

    with pytest.raises(TypeError, match="palette"):
        cast("Any", RawImage)(1, 1, ColorType.indexed, BitDepth.eight, bytes([0]), palette=palette)


def test_raw_image_rejects_bool_transparent_value() -> None:
    with pytest.raises(TypeError, match="transparent"):
        RawImage(1, 1, ColorType.grayscale, BitDepth.eight, bytes([0]), transparent=True)


def test_raw_image_rejects_rgb_transparency_above_bit_depth_range() -> None:
    with pytest.raises(ValueError, match="transparent"):
        RawImage(
            1,
            1,
            ColorType.rgb,
            BitDepth.eight,
            bytes([255, 0, 0]),
            transparent=(256, 0, 0),
        )


@pytest.mark.parametrize(
    "color_type", [ColorType.indexed, ColorType.grayscale_alpha, ColorType.rgba]
)
def test_raw_image_rejects_transparency_for_unsupported_color_types(color_type: ColorType) -> None:
    if color_type is ColorType.indexed:
        with pytest.raises(ValueError, match="transparent is not supported"):
            RawImage(
                1,
                1,
                color_type,
                BitDepth.eight,
                bytes([0]),
                transparent=0,
                palette=[(0, 0, 0)],
            )
    elif color_type is ColorType.grayscale_alpha:
        with pytest.raises(ValueError, match="transparent is not supported"):
            RawImage(1, 1, color_type, BitDepth.eight, bytes([0, 255]), transparent=0)
    else:
        with pytest.raises(ValueError, match="transparent is not supported"):
            RawImage(1, 1, color_type, BitDepth.eight, bytes([0, 0, 0, 255]), transparent=0)


def test_raw_image_invalid_data_length_raises_png_error() -> None:
    with pytest.raises(PngError, match="Data length"):
        RawImage(2, 2, ColorType.rgba, BitDepth.eight, b"too short")


def test_raw_image_invalid_palette_raises_value_error() -> None:
    with pytest.raises(ValueError, match="palette is required"):
        RawImage(1, 1, ColorType.indexed, BitDepth.eight, bytes([0]))


def test_raw_image_create_rejects_file_only_options() -> None:
    raw = RawImage(1, 1, ColorType.rgb, BitDepth.eight, bytes([255, 0, 0]))

    with pytest.raises(TypeError, match="unsupported option: backup"):
        cast("Any", raw.create_optimized_png)(backup=True)

    with pytest.raises(TypeError, match="unsupported option: preserve_attrs"):
        cast("Any", raw.create_optimized_png)(preserve_attrs=True)


def test_raw_image_rejects_negative_timeout() -> None:
    raw = RawImage(1, 1, ColorType.rgb, BitDepth.eight, bytes([255, 0, 0]))

    with pytest.raises(ValueError, match="timeout"):
        raw.create_optimized_png(timeout=-1)


def test_analyze_rejects_negative_timeout(png_path: Path) -> None:
    with pytest.raises(ValueError, match="timeout"):
        analyze(png_path, timeout=-1)


def test_optimize_from_memory_rejects_negative_timeout(png_bytes: bytes) -> None:
    with pytest.raises(ValueError, match="timeout"):
        optimize_from_memory(png_bytes, timeout=-1)


def test_enum_value_property_errors_are_propagated(png_bytes: bytes) -> None:
    with pytest.raises(RuntimeError, match="value property exploded"):
        cast("Any", optimize_from_memory)(png_bytes, filter=ExplodingValue())


def test_bit_depth_value_property_errors_are_propagated() -> None:
    with pytest.raises(RuntimeError, match="value property exploded"):
        cast("Any", RawImage)(1, 1, ColorType.rgb, ExplodingValue(), bytes([255, 0, 0]))
