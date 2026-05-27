"""Tests for examples shown in usage docs."""

from __future__ import annotations

import warnings
from typing import Any, cast

import pytest

from oxipng import (
    BitDepth,
    ColorType,
    Deflaters,
    FilterStrategy,
    Interlacing,
    RawImage,
    RowFilter,
    StripChunks,
    optimize_from_memory,
)

PYOXIPNG_WARNING = "pyoxipng compatibility path is unsupported"


def test_migration_guide_filter_strategy_examples(png_bytes: bytes) -> None:
    filter_value = FilterStrategy.none
    filters = FilterStrategy.predefined(["none", "sub", "up"])

    assert filter_value.value == "none"
    assert optimize_from_memory(data=png_bytes, filter=filters)


def test_migration_guide_rowfilter_example_warns() -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        filter_value = RowFilter.none

    assert filter_value.value == "none"


def test_migration_guide_interlacing_examples() -> None:
    assert Interlacing.off.value == "off"
    assert Interlacing.on.value == "on"

    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        assert Interlacing.Off.value == "off"
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        assert Interlacing.Adam7.value == "on"


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

    assert raw.create_optimized_png()


def test_migration_guide_pyoxipng_raw_image_order_warns() -> None:
    data = bytes([255, 0, 0, 255])
    width = 1
    height = 1

    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        raw = RawImage(data, width, height, color_type=ColorType.rgba())

    assert raw.create_optimized_png()


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
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        ColorType.rgba()
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        ColorType.rgb(None)
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        ColorType.indexed([(255, 0, 0)])


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

    assert optimized


def test_migration_guide_stable_factories_do_not_warn(png_bytes: bytes) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        strip = StripChunks.strip(["tEXt"])
        deflater = Deflaters.libdeflater(11)
        optimized = optimize_from_memory(data=png_bytes, strip=strip, deflate=deflater)

    assert optimized
