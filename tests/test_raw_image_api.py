"""RawImage public API tests."""

from typing import Any, TypeAlias, cast

import pytest

from oxipng import BitDepth, ColorType, PngError, RawImage, StripChunks
from tests.helpers.png import assert_png_structure, png_chunk_names, png_text_chunks
from tests.helpers.warnings import PYOXIPNG_WARNING, assert_no_deprecation_warning

Palette: TypeAlias = list[tuple[int, int, int] | tuple[int, int, int, int]]


def test_max_decompressed_size_optimizes_raw_image_without_warning() -> None:
    raw = RawImage(1, 1, ColorType.rgba, BitDepth.eight, bytes([255, 0, 0, 255]))

    output = assert_no_deprecation_warning(
        lambda: raw.create_optimized_png(max_decompressed_size=10_000_000)
    )
    assert_png_structure(output)


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

    output = assert_no_deprecation_warning(
        lambda: cast("Any", raw.create_optimized_png)(**{option: False})
    )
    assert_png_structure(output)


def test_raw_image_timeout_without_warning() -> None:
    raw = RawImage(1, 1, ColorType.rgba, BitDepth.eight, bytes([255, 0, 0, 255]))

    output = assert_no_deprecation_warning(lambda: raw.create_optimized_png(timeout=1.0))
    assert_png_structure(output)


def test_pyoxipng_raw_image_constructor_accepts_rgb_descriptor() -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        color_type = ColorType.rgb(None)
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        raw = RawImage(bytes([255, 0, 0]), 1, 1, color_type=color_type)

    output = raw.create_optimized_png()

    assert_png_structure(output)


def test_pyoxipng_raw_image_constructor_accepts_rgba_descriptor() -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        color_type = ColorType.rgba()
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        raw = RawImage(bytes([255, 0, 0, 255]), 1, 1, color_type=color_type)

    assert_png_structure(raw.create_optimized_png())


def test_pyoxipng_raw_image_constructor_default_signature_compat() -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        raw = RawImage(bytes([255, 0, 0, 255]), 1, 1)

    output = raw.create_optimized_png()

    assert_png_structure(output)


def test_pyoxipng_raw_image_constructor_with_compat_bit_depth() -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        color_type = ColorType.rgb()
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        raw = RawImage(
            bytes([255, 0, 0, 255, 0, 0]),
            1,
            1,
            color_type=color_type,
            bit_depth=BitDepth.sixteen,
        )

    output = raw.create_optimized_png()

    assert_png_structure(output)


def test_pyoxipng_raw_image_constructor_accepts_indexed_descriptor() -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        color_type = ColorType.indexed([(255, 0, 0)])
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        raw = RawImage(bytes([0]), 1, 1, color_type=color_type)

    assert_png_structure(raw.create_optimized_png())


def test_pyoxipng_raw_image_constructor_requires_compat_color_type() -> None:
    with (
        pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING),
        pytest.raises(TypeError, match="color_type"),
    ):
        cast("Any", RawImage)(bytes([255, 0, 0]), 1, 1, color_type="rgb")


def test_pyoxipng_raw_image_constructor_rejects_zero_dimensions() -> None:
    with (
        pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING),
        pytest.raises(ValueError, match="raw image dimensions"),
    ):
        RawImage(b"", 0, 1)


def test_raw_image_stable_constructor_rejects_zero_dimensions() -> None:
    with pytest.raises(ValueError, match="raw image dimensions"):
        RawImage(0, 1, ColorType.rgb, BitDepth.eight, b"")


def test_pyoxipng_raw_image_constructor_rejects_huge_dimensions_without_panic() -> None:
    with (
        pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING),
        pytest.raises(ValueError, match=r"raw image data length|image dimensions|too large"),
    ):
        RawImage(b"", 2**32 - 1, 2**32 - 1)


def test_stable_raw_image_constructor_does_not_warn() -> None:
    raw = assert_no_deprecation_warning(
        lambda: RawImage(1, 1, ColorType.rgb, BitDepth.eight, bytes([255, 0, 0]))
    )
    assert_png_structure(raw.create_optimized_png())


def test_stable_raw_image_constructor_accepts_keyword_arguments_without_warning() -> None:
    raw = assert_no_deprecation_warning(
        lambda: RawImage(
            width=1,
            height=1,
            color_type=ColorType.rgb,
            bit_depth=BitDepth.eight,
            data=bytes([255, 0, 0]),
        )
    )
    assert_png_structure(raw.create_optimized_png())


@pytest.mark.parametrize(
    ("color_type", "bit_depth"),
    [
        (ColorType.rgba, BitDepth.eight),
        (ColorType.rgb, BitDepth.eight),
        (ColorType.grayscale_alpha, BitDepth.sixteen),
        (ColorType.indexed, BitDepth.sixteen),
    ],
)
def test_raw_image_rejects_huge_dimensions_without_panic(
    color_type: ColorType, bit_depth: BitDepth
) -> None:
    if color_type is ColorType.indexed:
        with pytest.raises(ValueError, match=r"raw image data length|image dimensions|too large"):
            RawImage(
                2**32 - 1,
                2**32 - 1,
                color_type,
                bit_depth,
                b"",
                palette=[(0, 0, 0), (255, 255, 255)],
            )
    else:
        with pytest.raises(ValueError, match=r"raw image data length|image dimensions|too large"):
            RawImage(2**32 - 1, 2**32 - 1, color_type, bit_depth, b"")


@pytest.mark.parametrize(
    ("color_type", "bit_depth"),
    [
        (ColorType.rgba, BitDepth.eight),
        (ColorType.rgb, BitDepth.eight),
        (ColorType.indexed, BitDepth.sixteen),
    ],
)
def test_raw_image_rejects_non_bytes_data_before_overflow_validation(
    color_type: ColorType, bit_depth: BitDepth
) -> None:
    if color_type is ColorType.indexed:
        with pytest.raises(TypeError, match=r"data must be bytes, bytearray, or memoryview"):
            RawImage(
                2**32 - 1,
                2**32 - 1,
                color_type,
                bit_depth,
                cast("Any", 123),
                palette=[(0, 0, 0), (255, 255, 255)],
            )
    else:
        with pytest.raises(TypeError, match=r"data must be bytes, bytearray, or memoryview"):
            RawImage(2**32 - 1, 2**32 - 1, color_type, bit_depth, cast("Any", 123))


def test_stable_raw_image_constructor_with_positional_shape_and_keyword_data_does_not_warn() -> (
    None
):
    raw = assert_no_deprecation_warning(
        lambda: RawImage(
            1,
            1,
            ColorType.rgba,
            bit_depth=BitDepth.eight,
            data=bytes([255, 0, 0, 255]),
        )
    )
    assert_png_structure(raw.create_optimized_png())


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

    assert_png_structure(output)


def test_raw_image_accepts_string_color_type_and_integer_bit_depth() -> None:
    raw = RawImage(1, 1, "rgb", 8, bytes([255, 0, 0]))

    output = raw.create_optimized_png(level=1)

    assert_png_structure(output)


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

    assert_png_structure(output)


def test_raw_image_add_png_chunk_preserves_allowed_chunk() -> None:
    raw = RawImage(1, 1, ColorType.rgb, BitDepth.eight, bytes([255, 0, 0]))
    raw.add_png_chunk(b"tEXt", b"Comment\x00hello")

    output = raw.create_optimized_png(strip=StripChunks.none)

    assert png_text_chunks(output)["Comment"] == "hello"


def test_raw_image_add_icc_profile_writes_iccp_chunk() -> None:
    raw = RawImage(1, 1, ColorType.rgb, BitDepth.eight, bytes([255, 0, 0]))
    raw.add_icc_profile(b"not a real profile but stored as bytes")

    output = raw.create_optimized_png(strip=StripChunks.none)

    assert b"iCCP" in png_chunk_names(output)
    assert_png_structure(output)


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

    assert_png_structure(output)


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
