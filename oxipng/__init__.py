"""Python facade for the native oxipng extension."""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING
from warnings import warn

PYOXIPNG_COMPAT_WARNING = (
    "pyoxipng compatibility path is unsupported; migrate to oxipng-pybind's stable API."
)


def _warn_pyoxipng_compat() -> None:
    warn(PYOXIPNG_COMPAT_WARNING, DeprecationWarning, stacklevel=3)


class Interlacing(Enum):
    """PNG interlacing behavior."""

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
    def strip(names: list[str] | tuple[str, ...] | set[str]) -> "_CompatStripChunks":
        """Create a pyoxipng-compatible strip-chunk option; emits DeprecationWarning."""
        _warn_pyoxipng_compat()
        return _CompatStripChunks("strip", tuple(names))

    @staticmethod
    def keep(names: list[str] | tuple[str, ...] | set[str]) -> "_CompatStripChunks":
        """Create a pyoxipng-compatible keep-chunk option; emits DeprecationWarning."""
        _warn_pyoxipng_compat()
        return _CompatStripChunks("keep", tuple(names))


class Deflater(Enum):
    """DEFLATE backend."""

    libdeflater = "libdeflater"
    zopfli = "zopfli"


class Deflaters:
    """pyoxipng-compatible DEFLATE option factories."""

    @staticmethod
    def libdeflater(compression: int = 11) -> "_CompatDeflater":
        """Create a pyoxipng-compatible libdeflater option; emits DeprecationWarning."""
        _warn_pyoxipng_compat()
        return _CompatDeflater("libdeflater", compression)

    @staticmethod
    def zopfli(iterations: int = 15) -> "_CompatDeflater":
        """Create a pyoxipng-compatible zopfli option; emits DeprecationWarning."""
        _warn_pyoxipng_compat()
        return _CompatDeflater("zopfli", iterations)


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


class RowFilter(Enum):
    """pyoxipng-compatible row filter names."""

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


@dataclass(frozen=True)
class _CompatColorType:
    kind: str
    bit_depth: int
    palette: list[tuple[int, int, int] | tuple[int, int, int, int]] | None = None
    transparent: int | tuple[int, int, int] | None = None


@dataclass(frozen=True)
class _CompatStripChunks:
    mode: str
    names: tuple[str, ...]


@dataclass(frozen=True)
class _CompatDeflater:
    kind: str
    value: int


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
        transparent: int
        | tuple[int, int, int]
        | list[tuple[int, int, int] | tuple[int, int, int, int]]
        | None = None,
        *,
        bit_depth: int | BitDepth = BitDepth.eight,
    ) -> _CompatColorType:
        """Create a pyoxipng-compatible color descriptor; emits DeprecationWarning."""
        _warn_pyoxipng_compat()
        raw_bit_depth = bit_depth.value if isinstance(bit_depth, BitDepth) else bit_depth
        if self is ColorType.indexed:
            if not isinstance(transparent, list):
                raise ValueError("indexed color_type requires a palette")
            return _CompatColorType("indexed", raw_bit_depth, palette=list(transparent))
        if self in {ColorType.rgba, ColorType.grayscale_alpha}:
            if transparent is not None:
                raise ValueError(f"{self.value} does not accept transparent")
            return _CompatColorType(self.value, raw_bit_depth)
        if isinstance(transparent, list):
            raise TypeError(f"{self.value} does not accept palette")
        return _CompatColorType(self.value, raw_bit_depth, transparent=transparent)


ColorType.__call__.__doc__ = (
    "Create a pyoxipng-compatible color descriptor; emits DeprecationWarning."
)

if TYPE_CHECKING:
    from .__init__ import PngError, RawImage, optimize, optimize_from_memory
else:
    from _oxipng import PngError, RawImage, optimize, optimize_from_memory

__all__ = [
    "BitDepth",
    "ColorType",
    "Deflater",
    "Deflaters",
    "FilterStrategy",
    "Interlacing",
    "PngError",
    "RawImage",
    "RowFilter",
    "StripChunks",
    "optimize",
    "optimize_from_memory",
]
