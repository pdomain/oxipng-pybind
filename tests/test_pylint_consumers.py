"""Consumer lint compatibility tests."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import oxipng

if TYPE_CHECKING:
    from pathlib import Path


PUBLIC_API_NAMES = {
    "BitDepth",
    "ColorType",
    "Deflater",
    "Deflaters",
    "FilterStrategy",
    "Interlacing",
    "OptimizationResult",
    "PngError",
    "RawImage",
    "RowFilter",
    "StripChunks",
    "analyze",
    "optimize",
    "optimize_from_memory",
}


def test_pylint_consumer_public_facade_has_no_astroid_transform_warnings(
    tmp_path: Path,
) -> None:
    """Pylint consumers can inspect the public facade without Astroid recursion warnings."""
    assert set(oxipng.__all__) == PUBLIC_API_NAMES

    consumer = tmp_path / "consumer.py"
    consumer.write_text(
        """\
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


def run(path: str, data: bytes) -> bytes:
    interlace = Interlacing.keep
    deprecated_interlace = (Interlacing.Off, Interlacing.Adam7)
    strip = StripChunks.keep(["tEXt"])
    stripped = StripChunks.strip(["iTXt"])
    strip_factory = StripChunks.safe()
    deflater = Deflaters.libdeflater(12)
    zopfli = Deflaters.zopfli(15)
    deflater_member = Deflater.libdeflater
    filters = FilterStrategy.predefined(["none", "sub"])
    row_filters = (
        RowFilter.none,
        RowFilter.sub,
        RowFilter.up,
        RowFilter.average,
        RowFilter.paeth,
        RowFilter.minsum,
        RowFilter.entropy,
        RowFilter.bigrams,
        RowFilter.bigent,
        RowFilter.brute,
        RowFilter.NoOp,
        RowFilter.Sub,
        RowFilter.Up,
        RowFilter.Average,
        RowFilter.Paeth,
        RowFilter.MinSum,
        RowFilter.Entropy,
        RowFilter.Bigrams,
        RowFilter.BigEnt,
        RowFilter.Brute,
    )
    color_types = (
        ColorType.rgb((255, 0, 0)),
        ColorType.rgba(),
        ColorType.indexed([(255, 0, 0)]),
        ColorType.grayscale(None),
        ColorType.grayscale_alpha(),
    )
    raw = RawImage(1, 1, ColorType.rgba, BitDepth.eight, bytes([255, 0, 0, 255]))
    raw.add_png_chunk(b"tEXt", b"Comment\\x00hello")
    raw.add_icc_profile(b"profile")
    raw_png = raw.create_optimized_png(filter=(FilterStrategy.none, "sub"))
    result = analyze(path, interlace=interlace, strip=strip, deflate=deflater, filter=filters)
    assert isinstance(result, OptimizationResult)
    try:
        optimize(path, level=2, strip=stripped, deflate=zopfli, filter=[FilterStrategy.none])
    except PngError:
        pass
    _ = (
        deprecated_interlace,
        strip_factory,
        deflater_member,
        row_filters,
        color_types,
        raw_png,
    )
    return optimize_from_memory(data, filter=(FilterStrategy.none, "sub"))
""",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603 - fixed command exercises consumer Pylint.
        [
            sys.executable,
            "-m",
            "pylint",
            "--exit-zero",
            str(consumer),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert "Astroid was unable to transform" not in result.stderr
    assert "system recursion limit is lifted" not in result.stderr
