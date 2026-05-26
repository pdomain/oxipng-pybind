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


if TYPE_CHECKING:
    from .__init__ import PngError, optimize, optimize_from_memory
else:
    from _oxipng import PngError, optimize, optimize_from_memory

__all__ = [
    "Deflater",
    "FilterStrategy",
    "Interlacing",
    "PngError",
    "StripChunks",
    "optimize",
    "optimize_from_memory",
]
