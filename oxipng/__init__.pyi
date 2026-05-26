"""Typing stub for the supported oxipng-pybind API."""

from enum import Enum
from os import PathLike

StrOrBytesPath = str | bytes | PathLike[str] | PathLike[bytes]
BytesLike = bytes | bytearray | memoryview

class Interlacing(Enum):
    keep = "keep"
    off = "off"
    on = "on"

class StripChunks(Enum):
    none = "none"
    safe = "safe"
    all = "all"

class Deflater(Enum):
    libdeflater = "libdeflater"
    zopfli = "zopfli"

class FilterStrategy(Enum):
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
    grayscale = "grayscale"
    rgb = "rgb"
    indexed = "indexed"
    grayscale_alpha = "grayscale_alpha"
    rgba = "rgba"

class BitDepth(Enum):
    one = 1
    two = 2
    four = 4
    eight = 8
    sixteen = 16

class PngError(Exception):
    """Raised when oxipng cannot optimize the input PNG."""

class RawImage:
    def __init__(
        self,
        width: int,
        height: int,
        color_type: ColorType | str,
        bit_depth: BitDepth | int,
        data: BytesLike,
        *,
        palette: list[tuple[int, int, int] | tuple[int, int, int, int]] | None = None,
        transparent: int | tuple[int, int, int] | None = None,
    ) -> None:
        """Create a raw image from packed pixel data."""

    def add_png_chunk(self, name: BytesLike, data: BytesLike) -> None:
        """Add an auxiliary PNG chunk."""

    def add_icc_profile(self, data: BytesLike) -> None:
        """Add an ICC profile."""

    def create_optimized_png(
        self,
        *,
        level: int = 2,
        interlace: Interlacing | str | None = None,
        strip: StripChunks | str | None = None,
        deflate: Deflater | str | None = None,
        filter: FilterStrategy
        | str
        | list[FilterStrategy | str]
        | tuple[FilterStrategy | str, ...]
        | None = None,
        fix_errors: bool = False,
        force: bool = False,
    ) -> bytes:
        """Return optimized PNG bytes."""

def optimize(
    input: StrOrBytesPath,
    output: StrOrBytesPath | None = None,
    *,
    level: int = 2,
    interlace: Interlacing | str | None = None,
    strip: StripChunks | str | None = None,
    deflate: Deflater | str | None = None,
    filter: FilterStrategy
    | str
    | list[FilterStrategy | str]
    | tuple[FilterStrategy | str, ...]
    | None = None,
    fix_errors: bool = False,
    force: bool = False,
    backup: bool = False,
    preserve_attrs: bool = False,
) -> None:
    """Optimize a PNG file on disk."""

def optimize_from_memory(
    data: BytesLike,
    *,
    level: int = 2,
    interlace: Interlacing | str | None = None,
    strip: StripChunks | str | None = None,
    deflate: Deflater | str | None = None,
    filter: FilterStrategy
    | str
    | list[FilterStrategy | str]
    | tuple[FilterStrategy | str, ...]
    | None = None,
    fix_errors: bool = False,
    force: bool = False,
) -> bytes:
    """Optimize PNG bytes in memory."""
