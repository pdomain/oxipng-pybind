"""Python facade for the native oxipng extension."""

from collections.abc import Iterator, Sequence
from enum import Enum
from typing import TYPE_CHECKING, cast

from . import _pyoxipng_compat as _compat


class Interlacing(Enum, metaclass=_compat.PyoxipngCompatEnumMeta):
    """PNG interlacing behavior."""

    __pyoxipng_deprecated_names__ = frozenset({"Off", "Adam7"})

    keep = "keep"
    off = "off"
    on = "on"
    Off = "off"
    Adam7 = "on"


class StripChunks(Enum):
    """Metadata stripping behavior."""

    none = "none"
    safe = "safe"
    all = "all"

    @staticmethod
    def strip(names: list[str] | tuple[str, ...] | set[str]) -> _compat.CompatStripChunks:
        """Create a strip-chunk option for explicit PNG chunk names."""
        return _compat.CompatStripChunks("strip", tuple(names))

    @staticmethod
    def keep(names: list[str] | tuple[str, ...] | set[str]) -> _compat.CompatStripChunks:
        """Create a keep-chunk option for explicit PNG chunk names."""
        return _compat.CompatStripChunks("keep", tuple(names))


class Deflater(Enum):
    """DEFLATE backend."""

    libdeflater = "libdeflater"
    zopfli = "zopfli"


class Deflaters:
    """DEFLATE option factories."""

    @staticmethod
    def libdeflater(compression: int = 11) -> _compat.CompatDeflater:
        """Create a libdeflater option with an explicit compression level."""
        return _compat.CompatDeflater("libdeflater", compression)

    @staticmethod
    def zopfli(iterations: int = 15) -> _compat.CompatDeflater:
        """Create a zopfli option with an explicit iteration count."""
        return _compat.CompatDeflater("zopfli", iterations)


class FilterStrategy(Enum):
    """PNG row filter strategy."""

    none = "none"
    sub = "sub"
    up = "up"
    average = "average"
    paeth = "paeth"
    minsum = "minsum"
    entropy = "entropy"
    bigrams = "bigrams"
    bigent = "bigent"
    brute = "brute"

    @staticmethod
    def predefined(filters: Sequence[object] | Iterator[object]) -> _compat.PredefinedFilters:
        """Create a predefined row-filter sequence."""
        _compat.reject_unordered_predefined_filters(filters)
        parsed = tuple(_compat.basic_row_filter_value(filter_value) for filter_value in filters)
        if not parsed:
            raise ValueError("predefined filter must not be empty")
        return _compat.PredefinedFilters(parsed)


class RowFilter(Enum, metaclass=_compat.PyoxipngCompatEnumMeta):
    """PNG row filter names."""

    __pyoxipng_deprecated_names__ = frozenset(
        {
            "none",
            "sub",
            "up",
            "average",
            "paeth",
            "minsum",
            "entropy",
            "bigrams",
            "bigent",
            "brute",
        }
    )

    none = "none"
    sub = "sub"
    up = "up"
    average = "average"
    paeth = "paeth"
    minsum = "minsum"
    entropy = "entropy"
    bigrams = "bigrams"
    bigent = "bigent"
    brute = "brute"


class BitDepth(Enum):
    """Raw image bit depth."""

    one = 1
    two = 2
    four = 4
    eight = 8
    sixteen = 16


class ColorType(Enum):
    """Raw image color type."""

    grayscale = "grayscale"
    rgb = "rgb"
    indexed = "indexed"
    grayscale_alpha = "grayscale_alpha"
    rgba = "rgba"

    def __call__(
        self,
        transparent: int | tuple[int, int, int] | Sequence[Sequence[int]] | None = None,
        *,
        bit_depth: int | BitDepth = BitDepth.eight,
    ) -> _compat.CompatColorType:
        """Create a pyoxipng-compatible color descriptor; emits DeprecationWarning."""
        _compat.warn_pyoxipng_compat()
        raw_bit_depth = bit_depth.value if isinstance(bit_depth, BitDepth) else bit_depth
        if self is ColorType.indexed:
            if transparent is None:
                raise ValueError("indexed color_type requires a palette")
            palette = _compat.ordered_palette_sequence(transparent, "indexed palette")
            palette_snapshot = tuple(tuple(cast("Sequence[int]", color)) for color in palette)
            return _compat.CompatColorType(
                "indexed",
                raw_bit_depth,
                palette=palette_snapshot,
            )
        if self in {ColorType.rgba, ColorType.grayscale_alpha}:
            if transparent is not None:
                raise ValueError(f"{self.value} does not accept transparent")
            return _compat.CompatColorType(self.value, raw_bit_depth)
        if isinstance(transparent, list):
            raise TypeError(f"{self.value} does not accept palette")
        return _compat.CompatColorType(
            self.value,
            raw_bit_depth,
            transparent=cast("int | tuple[int, int, int] | None", transparent),
        )


ColorType.__call__.__doc__ = (
    "Create a pyoxipng-compatible color descriptor; emits DeprecationWarning."
)

if TYPE_CHECKING:
    from .__init__ import (
        OptimizationResult,
        PngError,
        RawImage,
        analyze,
        optimize,
        optimize_from_memory,
    )
else:
    from _oxipng import (
        OptimizationResult,
        PngError,
        RawImage,
        analyze,
        optimize,
        optimize_from_memory,
    )

__all__ = [
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
]
