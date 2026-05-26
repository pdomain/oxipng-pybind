"""Python facade for the native oxipng extension."""

from enum import Enum
from typing import TYPE_CHECKING


class Interlacing(Enum):
    """PNG interlacing behavior."""

    keep = "keep"
    off = "off"
    on = "on"


class StripChunks(Enum):
    """Metadata stripping behavior."""

    none = "none"
    safe = "safe"
    all = "all"


class Deflater(Enum):
    """DEFLATE backend."""

    libdeflater = "libdeflater"
    zopfli = "zopfli"


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


class ColorType(Enum):
    """Raw image color type."""

    grayscale = "grayscale"
    rgb = "rgb"
    indexed = "indexed"
    grayscale_alpha = "grayscale_alpha"
    rgba = "rgba"


class BitDepth(Enum):
    """Raw image bit depth."""

    one = 1
    two = 2
    four = 4
    eight = 8
    sixteen = 16


if TYPE_CHECKING:
    from .__init__ import PngError, RawImage, optimize, optimize_from_memory
else:
    from _oxipng import PngError, RawImage, optimize, optimize_from_memory

__all__ = [
    "BitDepth",
    "ColorType",
    "Deflater",
    "FilterStrategy",
    "Interlacing",
    "PngError",
    "RawImage",
    "StripChunks",
    "optimize",
    "optimize_from_memory",
]
