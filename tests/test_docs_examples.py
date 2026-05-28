"""Tests for examples shown in usage docs."""

from __future__ import annotations

import sys
from io import BytesIO
from typing import TYPE_CHECKING, Any, cast

import pytest

from oxipng import (
    BitDepth,
    ColorType,
    Deflaters,
    FilterStrategy,
    Interlacing,
    PngError,
    RawImage,
    RowFilter,
    StripChunks,
    analyze,
    optimize,
    optimize_from_memory,
)
from tests.helpers.png import (
    assert_png_path,
    assert_png_structure,
    png_chunk_names,
    png_text_chunks,
)
from tests.helpers.warnings import (
    PYOXIPNG_WARNING,
    assert_no_deprecation_warning,
    assert_pyoxipng_warning,
)

if TYPE_CHECKING:
    from pathlib import Path


class _Stream:
    buffer: BytesIO

    def __init__(self, data: bytes = b"") -> None:
        self.buffer = BytesIO(data)


def test_file_optimization_basic_use_example(tmp_path: Path, png_bytes: bytes) -> None:
    input_path = tmp_path / "cover.png"
    output_path = tmp_path / "cover.optimized.png"
    input_path.write_bytes(png_bytes)

    optimize(input=input_path, output=output_path, strip="safe")

    assert_png_path(output_path)


def test_file_optimization_analyze_example(tmp_path: Path, png_bytes: bytes) -> None:
    input_path = tmp_path / "cover.png"
    input_path.write_bytes(png_bytes)

    result = analyze(input=input_path, strip="safe")

    assert result.original_size > 0
    assert result.optimized_size > 0


def test_file_optimization_backup_example(tmp_path: Path, png_bytes: bytes) -> None:
    input_path = tmp_path / "cover.png"
    input_path.write_bytes(png_bytes)

    optimize(input=input_path, backup=True, force=True)

    assert input_path.with_name("cover.png.bak").read_bytes() == png_bytes


def test_file_optimization_preserve_attrs_example(tmp_path: Path, png_bytes: bytes) -> None:
    input_path = tmp_path / "cover.png"
    output_path = tmp_path / "out.png"
    input_path.write_bytes(png_bytes)

    optimize(input=input_path, output=output_path, preserve_attrs=True)

    assert_png_path(output_path)


def test_file_optimization_error_example(tmp_path: Path) -> None:
    input_path = tmp_path / "possibly-corrupt.png"
    input_path.write_bytes(b"not a png")

    handled = False
    try:
        optimize(input=input_path, fix_errors=False)
    except PngError:
        handled = True

    assert handled


def test_memory_optimization_basic_use_example(tmp_path: Path, png_bytes: bytes) -> None:
    input_path = tmp_path / "cover.png"
    output_path = tmp_path / "cover.optimized.png"
    input_path.write_bytes(png_bytes)

    png_bytes = input_path.read_bytes()
    optimized = optimize_from_memory(data=png_bytes, level=4, strip="safe")
    output_path.write_bytes(optimized)

    assert_png_path(output_path)


def test_memory_optimization_inputs_example(png_bytes: bytes) -> None:
    optimized_from_bytearray = optimize_from_memory(data=bytearray(png_bytes))
    optimized_from_view = optimize_from_memory(data=memoryview(png_bytes))

    assert_png_structure(optimized_from_bytearray)
    assert_png_structure(optimized_from_view)


def test_memory_optimization_stdin_stdout_example(
    monkeypatch: pytest.MonkeyPatch, png_bytes: bytes
) -> None:
    stdin = _Stream(png_bytes)
    stdout = _Stream()
    monkeypatch.setattr(sys, "stdin", stdin)
    monkeypatch.setattr(sys, "stdout", stdout)

    data = sys.stdin.buffer.read()
    optimized = optimize_from_memory(data=data)
    sys.stdout.buffer.write(optimized)

    assert_png_structure(stdout.buffer.getvalue())


def test_memory_optimization_error_example() -> None:
    handled = False
    try:
        optimize_from_memory(data=b"not a png")
    except PngError:
        handled = True

    assert handled


def test_untrusted_input_memory_limits_example(png_bytes: bytes) -> None:
    optimized = optimize_from_memory(data=png_bytes, timeout=2.0, max_decompressed_size=50_000_000)

    assert_png_structure(optimized)


def test_untrusted_input_file_limits_example(tmp_path: Path, png_bytes: bytes) -> None:
    input_path = tmp_path / "upload.png"
    input_path.write_bytes(png_bytes)

    optimize(input=input_path, timeout=2.0, max_decompressed_size=50_000_000)

    assert_png_path(input_path)


def test_untrusted_input_byte_stream_example(
    monkeypatch: pytest.MonkeyPatch, png_bytes: bytes
) -> None:
    stdin = _Stream(png_bytes)
    stdout = _Stream()
    monkeypatch.setattr(sys, "stdin", stdin)
    monkeypatch.setattr(sys, "stdout", stdout)

    data = sys.stdin.buffer.read()
    optimized = optimize_from_memory(data=data, timeout=2.0, max_decompressed_size=50_000_000)
    sys.stdout.buffer.write(optimized)

    assert_png_structure(stdout.buffer.getvalue())


def test_raw_image_basic_use_example() -> None:
    raw = RawImage(
        width=1,
        height=1,
        color_type=ColorType.rgba,
        bit_depth=BitDepth.eight,
        data=bytes([255, 0, 0, 255]),
    )
    png_bytes = raw.create_optimized_png(level=3)

    assert_png_structure(png_bytes)


def test_raw_image_indexed_example() -> None:
    raw = RawImage(
        width=2,
        height=1,
        color_type="indexed",
        bit_depth=8,
        data=bytes([0, 1]),
        palette=[(255, 0, 0), (0, 0, 255, 128)],
    )
    png_bytes = raw.create_optimized_png()

    assert_png_structure(png_bytes)


def test_raw_image_transparency_example() -> None:
    gray = RawImage(
        width=1,
        height=1,
        color_type=ColorType.grayscale,
        bit_depth=BitDepth.eight,
        data=bytes([0]),
        transparent=0,
    )
    rgb = RawImage(
        width=1,
        height=1,
        color_type=ColorType.rgb,
        bit_depth=BitDepth.eight,
        data=bytes([255, 0, 0]),
        transparent=(255, 0, 0),
    )

    assert_png_structure(gray.create_optimized_png())
    assert_png_structure(rgb.create_optimized_png())


def test_raw_image_png_chunk_example() -> None:
    raw = RawImage(
        width=1,
        height=1,
        color_type=ColorType.grayscale,
        bit_depth=BitDepth.eight,
        data=bytes([0]),
    )
    raw.add_png_chunk(b"tEXt", b"Comment\x00created from raw pixels")
    png_bytes = raw.create_optimized_png()

    assert png_text_chunks(png_bytes)["Comment"] == "created from raw pixels"


def test_raw_image_icc_profile_example() -> None:
    icc_profile_bytes = b"example ICC profile bytes"
    raw = RawImage(
        width=1,
        height=1,
        color_type=ColorType.grayscale,
        bit_depth=BitDepth.eight,
        data=bytes([0]),
    )
    raw.add_icc_profile(icc_profile_bytes)
    png_bytes = raw.create_optimized_png()

    assert b"iCCP" in png_chunk_names(png_bytes)


def test_raw_image_error_example() -> None:
    handled = False
    try:
        RawImage(
            width=1,
            height=1,
            color_type=ColorType.rgb,
            bit_depth=BitDepth.eight,
            data=bytes([255]),
        )
    except PngError:
        handled = True

    assert handled


def test_migration_guide_filter_strategy_examples(png_bytes: bytes) -> None:
    filter_value = FilterStrategy.none
    filters = FilterStrategy.predefined(["none", "sub", "up"])

    assert filter_value.value == "none"
    assert_png_structure(optimize_from_memory(data=png_bytes, filter=filters))


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("none", "none"),
        ("sub", "sub"),
        ("up", "up"),
        ("average", "average"),
        ("paeth", "paeth"),
        ("minsum", "minsum"),
        ("entropy", "entropy"),
        ("bigrams", "bigrams"),
        ("bigent", "bigent"),
        ("brute", "brute"),
        ("NoOp", "none"),
        ("Sub", "sub"),
        ("Up", "up"),
        ("Average", "average"),
        ("Paeth", "paeth"),
        ("MinSum", "minsum"),
        ("Entropy", "entropy"),
        ("Bigrams", "bigrams"),
        ("BigEnt", "bigent"),
        ("Brute", "brute"),
    ],
)
def test_migration_guide_rowfilter_example_warns(name: str, value: str) -> None:
    filter_value = assert_pyoxipng_warning(lambda: getattr(RowFilter, name))

    assert filter_value.value == value


def test_migration_guide_interlacing_examples() -> None:
    assert Interlacing.off.value == "off"
    assert Interlacing.on.value == "on"

    assert assert_pyoxipng_warning(lambda: Interlacing.Off).value == "off"
    assert assert_pyoxipng_warning(lambda: Interlacing.Adam7).value == "on"


def test_migration_guide_stable_raw_image_example() -> None:
    data = bytes([255, 0, 0, 255])
    width = 1
    height = 1

    raw = RawImage(
        width=width,
        height=height,
        color_type=ColorType.rgba,
        bit_depth=BitDepth.eight,
        data=data,
    )

    assert_png_structure(raw.create_optimized_png())


def test_migration_guide_pyoxipng_raw_image_order_warns() -> None:
    data = bytes([255, 0, 0, 255])
    width = 1
    height = 1

    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        raw = RawImage(data, width, height, color_type=ColorType.rgba())

    assert_png_structure(raw.create_optimized_png())


def test_migration_guide_rejected_raw_image_shape() -> None:
    data = bytes([255, 0, 0, 255])
    width = 1
    height = 1

    with (
        pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING),
        pytest.raises(TypeError, match="color_type must be created"),
    ):
        RawImage(data, width, height, color_type=cast("Any", ColorType.rgba))


def test_migration_guide_color_type_factory_examples_warn() -> None:
    assert_pyoxipng_warning(ColorType.rgba)
    assert_pyoxipng_warning(lambda: ColorType.rgb(None))
    assert_pyoxipng_warning(lambda: ColorType.indexed([(255, 0, 0)]))


def test_migration_guide_other_options_examples(png_bytes: bytes) -> None:
    optimized = optimize_from_memory(
        data=png_bytes,
        optimize_alpha=True,
        bit_depth_reduction=True,
        color_type_reduction=True,
        palette_reduction=True,
        grayscale_reduction=True,
        idat_recoding=True,
        scale_16=True,
        fast_evaluation=False,
        timeout=10,
        max_decompressed_size=256 * 1024 * 1024,
    )

    assert_png_structure(optimized)


def test_migration_guide_stable_factories_do_not_warn(png_bytes: bytes) -> None:
    def run_example() -> bytes:
        strip = StripChunks.strip(["tEXt"])
        deflater = Deflaters.libdeflater(11)
        return optimize_from_memory(data=png_bytes, strip=strip, deflate=deflater)

    assert_png_structure(assert_no_deprecation_warning(run_example))
