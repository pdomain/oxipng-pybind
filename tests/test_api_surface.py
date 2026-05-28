"""Supported public API surface tests."""

import inspect

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
    StripChunks,
    analyze,
    optimize,
    optimize_from_memory,
)


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
