"""Supported public API tests."""

import inspect
from io import BytesIO
from pathlib import Path
from typing import Any, cast

import pytest
from PIL import Image

from oxipng import (
    BitDepth,
    ColorType,
    Deflater,
    FilterStrategy,
    Interlacing,
    PngError,
    RawImage,
    StripChunks,
    optimize,
    optimize_from_memory,
)


def assert_readable_png_path(path: Path) -> None:
    """Assert that Pillow can read the optimized PNG."""
    with Image.open(path) as image:
        image.verify()


def assert_readable_png_bytes(data: bytes) -> None:
    """Assert that Pillow can read optimized PNG bytes."""
    with Image.open(BytesIO(data)) as image:
        image.verify()


def test_import_supported_api() -> None:
    assert callable(optimize)
    assert callable(optimize_from_memory)
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
        "filter=None, fix_errors=False, force=False, backup=False, preserve_attrs=False)"
    )


def test_optimize_from_memory_signature_matches_supported_api() -> None:
    assert str(inspect.signature(optimize_from_memory)) == (
        "(data, *, level=2, interlace=None, strip=None, deflate=None, filter=None, "
        "fix_errors=False, force=False)"
    )


def test_optimize_in_place_with_high_compression_level(png_path: Path) -> None:
    optimize(png_path, level=6)

    assert_readable_png_path(png_path)


def test_optimize_to_output_path(png_path: Path, tmp_path: Path) -> None:
    output = tmp_path / "optimized.png"
    optimize(png_path, output, level=6)

    assert output.exists()
    assert_readable_png_path(output)
    assert_readable_png_path(png_path)


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


def test_corrupt_memory_input_raises_png_error() -> None:
    with pytest.raises(PngError):
        optimize_from_memory(b"not a png")


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


@pytest.mark.parametrize("name", [b"IHDR", b"IDAT", b"IEND", b"PLTE", b"tRNS", b"iCCP"])
def test_raw_image_rejects_structural_or_dedicated_chunks(name: bytes) -> None:
    raw = RawImage(1, 1, ColorType.rgba, BitDepth.eight, bytes([255, 0, 0, 255]))

    with pytest.raises(ValueError, match="chunk name"):
        raw.add_png_chunk(name, b"payload")


@pytest.mark.parametrize("name", [b"abc", b"abcde", b"ab1d", b"ab_d", b"ab\x00d", b"abCd"])
def test_raw_image_rejects_invalid_chunk_names(name: bytes) -> None:
    raw = RawImage(1, 1, ColorType.rgba, BitDepth.eight, bytes([255, 0, 0, 255]))

    with pytest.raises(ValueError, match="chunk name"):
        raw.add_png_chunk(name, b"payload")


def test_raw_image_rejects_too_many_palette_entries_for_bit_depth() -> None:
    palette = [(index, index, index) for index in range(5)]

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
    kwargs: dict[str, object] = {}
    data = bytes([0])
    if color_type is ColorType.indexed:
        kwargs["palette"] = [(0, 0, 0)]
    elif color_type is ColorType.grayscale_alpha:
        data = bytes([0, 255])
    else:
        data = bytes([0, 0, 0, 255])

    with pytest.raises(ValueError, match="transparent is not supported"):
        RawImage(1, 1, color_type, BitDepth.eight, data, transparent=0, **kwargs)


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
