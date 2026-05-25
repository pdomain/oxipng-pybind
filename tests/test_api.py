"""Supported public API tests."""

import inspect
from pathlib import Path
from typing import Any, cast

import pytest
from PIL import Image

from oxipng import PngError, optimize


def assert_readable_png(path: Path) -> None:
    """Assert that Pillow can read the optimized PNG."""
    with Image.open(path) as image:
        image.verify()


def test_import_supported_api() -> None:
    assert callable(optimize)
    assert issubclass(PngError, Exception)


def test_optimize_signature_matches_supported_api() -> None:
    assert str(inspect.signature(optimize)) == "(input, output=None, *, level=2)"


def test_optimize_in_place_with_standard_ebooks_level(png_path: Path) -> None:
    optimize(png_path, level=6)

    assert_readable_png(png_path)


def test_optimize_to_output_path(png_path: Path, tmp_path: Path) -> None:
    output = tmp_path / "optimized.png"
    optimize(png_path, output, level=6)

    assert output.exists()
    assert_readable_png(output)
    assert_readable_png(png_path)


@pytest.mark.parametrize("level", [-1, 7])
def test_invalid_level_raises_value_error(png_path: Path, level: int) -> None:
    with pytest.raises(ValueError, match="level must be between 0 and 6"):
        optimize(png_path, level=level)


def test_unsupported_keyword_raises_type_error(png_path: Path) -> None:
    with pytest.raises(TypeError, match="unsupported option: strip"):
        cast("Any", optimize)(png_path, level=6, strip="safe")


def test_corrupt_input_raises_png_error(corrupt_png_path: Path) -> None:
    with pytest.raises(PngError):
        optimize(corrupt_png_path, level=6)
