"""File optimize and analyze public API tests."""

import os
import warnings
from pathlib import Path
from typing import Any, cast

import pytest

from oxipng import (
    Deflater,
    FilterStrategy,
    Interlacing,
    OptimizationResult,
    PngError,
    StripChunks,
    analyze,
    optimize,
)
from tests.helpers.png import assert_png_path


class CustomPathLike:
    path: Path

    def __init__(self, path: Path) -> None:
        self.path = path

    def __fspath__(self) -> str:
        return str(self.path)


def test_optimize_in_place_with_high_compression_level(png_path: Path) -> None:
    optimize(png_path, level=6)

    assert_png_path(png_path)


def test_optimize_to_output_path_does_not_modify_input(
    png_path: Path,
    tmp_path: Path,
) -> None:
    original = png_path.read_bytes()
    output = tmp_path / "optimized.png"

    optimize(png_path, output, level=6)

    assert output.exists()
    assert_png_path(output)
    assert png_path.read_bytes() == original


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

    assert_png_path(output)


def test_optimize_accepts_custom_pathlike(png_path: Path, tmp_path: Path) -> None:
    output = tmp_path / "out.png"

    optimize(CustomPathLike(png_path), CustomPathLike(output))

    assert_png_path(output)


def test_optimize_interlace_keep_is_accepted(png_path: Path) -> None:
    optimize(png_path, interlace=Interlacing.keep)

    assert_png_path(png_path)


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

    assert_png_path(png_path)


def test_max_decompressed_size_optimizes_file_without_warning(png_path: Path) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        optimize(png_path, max_decompressed_size=10_000_000)

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    assert_png_path(png_path)


@pytest.mark.parametrize("level", [-1, 7])
def test_invalid_level_raises_value_error(png_path: Path, level: int) -> None:
    with pytest.raises(ValueError, match="level must be between 0 and 6"):
        optimize(png_path, level=level)


@pytest.mark.parametrize("value", [True, False])
def test_optimize_level_rejects_bool(png_path: Path, value: bool) -> None:
    with pytest.raises(TypeError, match="level must be an integer"):
        optimize(png_path, level=value)


@pytest.mark.parametrize("value", [True, False])
def test_analyze_level_rejects_bool(png_path: Path, value: bool) -> None:
    with pytest.raises(TypeError, match="level must be an integer"):
        analyze(png_path, level=value)


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
    assert_png_path(png_path)


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
    assert_png_path(output)


def test_corrupt_input_raises_png_error(corrupt_png_path: Path) -> None:
    with pytest.raises(PngError):
        optimize(corrupt_png_path, level=6)


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


def test_analyze_rejects_negative_timeout(png_path: Path) -> None:
    with pytest.raises(ValueError, match="timeout"):
        analyze(png_path, timeout=-1)
