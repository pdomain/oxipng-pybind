"""pyoxipng compatibility API tests."""

import warnings
from pathlib import Path

import pytest

from oxipng import (
    BitDepth,
    ColorType,
    Deflaters,
    FilterStrategy,
    Interlacing,
    RowFilter,
    StripChunks,
    optimize,
)
from tests.helpers.png import assert_png_path
from tests.helpers.warnings import PYOXIPNG_WARNING


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
def test_pyoxipng_rowfilter_aliases_warn_on_access(name: str, value: str) -> None:
    with pytest.warns(DeprecationWarning, match=PYOXIPNG_WARNING):
        row_filter = getattr(RowFilter, name)
    assert row_filter.value == value


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
        keep = StripChunks.keep(["iCCP"])
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


def test_pyoxipng_strip_factories_optimize_file(png_path: Path) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        strip = StripChunks.strip(["tEXt"])

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    optimize(png_path, strip=strip)

    assert_png_path(png_path)


def test_pyoxipng_keep_factories_optimize_file(png_path: Path) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        keep = StripChunks.keep({"iCCP"})

    assert [warning for warning in caught if issubclass(warning.category, DeprecationWarning)] == []
    optimize(png_path, strip=keep)

    assert_png_path(png_path)


@pytest.mark.parametrize("value", [True, False])
def test_deflater_libdeflater_bool_is_compatibility_path(value: bool) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        Deflaters.libdeflater(value)

    matches = [
        warning
        for warning in caught
        if issubclass(warning.category, DeprecationWarning)
        and PYOXIPNG_WARNING in str(warning.message)
    ]
    assert len(matches) == 1


@pytest.mark.parametrize("value", [True, False])
def test_deflater_zopfli_bool_is_compatibility_path(value: bool) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if value:
            Deflaters.zopfli(value)
        else:
            with pytest.raises(TypeError, match="must be an integer"):
                Deflaters.zopfli(value)

    matches = [
        warning
        for warning in caught
        if issubclass(warning.category, DeprecationWarning)
        and PYOXIPNG_WARNING in str(warning.message)
    ]
    assert len(matches) == 1
