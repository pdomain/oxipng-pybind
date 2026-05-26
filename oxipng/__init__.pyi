"""Typing stub for the supported oxipng-pybind API."""

from enum import Enum
from os import PathLike

StrOrBytesPath = str | bytes | PathLike[str] | PathLike[bytes]
BytesLike = bytes | bytearray | memoryview

class Interlacing(Enum):
    keep = "keep"
    off = "off"
    on = "on"
    Off = "off"
    Adam7 = "on"

class StripChunks(Enum):
    none = "none"
    safe = "safe"
    all = "all"

    @staticmethod
    def strip(names: list[str] | tuple[str, ...] | set[str]) -> _CompatStripChunks:
        """Create a pyoxipng-compatible strip-chunk option; emits DeprecationWarning."""

    @staticmethod
    def keep(names: list[str] | tuple[str, ...] | set[str]) -> _CompatStripChunks:
        """Create a pyoxipng-compatible keep-chunk option; emits DeprecationWarning."""

class Deflater(Enum):
    libdeflater = "libdeflater"
    zopfli = "zopfli"

class Deflaters:
    @staticmethod
    def libdeflater(compression: int = 11) -> _CompatDeflater:
        """Create a pyoxipng-compatible libdeflater option; emits DeprecationWarning."""

    @staticmethod
    def zopfli(iterations: int = 15) -> _CompatDeflater:
        """Create a pyoxipng-compatible zopfli option; emits DeprecationWarning."""

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

class RowFilter(Enum):
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

FilterOption = FilterStrategy | RowFilter | str

class _CompatColorType:
    kind: str
    bit_depth: int
    palette: list[tuple[int, int, int] | tuple[int, int, int, int]] | None
    transparent: int | tuple[int, int, int] | None

class _CompatStripChunks:
    mode: str
    names: tuple[str, ...]

class _CompatDeflater:
    kind: str
    value: int

class BitDepth(Enum):
    one = 1
    two = 2
    four = 4
    eight = 8
    sixteen = 16

class ColorType(Enum):
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
        bit_depth: BitDepth | int = BitDepth.eight,
    ) -> _CompatColorType:
        """Create a pyoxipng-compatible color descriptor; emits DeprecationWarning."""

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
        strip: StripChunks | _CompatStripChunks | str | None = None,
        deflate: Deflater | _CompatDeflater | str | None = None,
        filter: FilterOption
        | list[FilterOption]
        | tuple[FilterOption, ...]
        | set[FilterOption]
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
    strip: StripChunks | _CompatStripChunks | str | None = None,
    deflate: Deflater | _CompatDeflater | str | None = None,
    filter: FilterOption
    | list[FilterOption]
    | tuple[FilterOption, ...]
    | set[FilterOption]
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
    strip: StripChunks | _CompatStripChunks | str | None = None,
    deflate: Deflater | _CompatDeflater | str | None = None,
    filter: FilterOption
    | list[FilterOption]
    | tuple[FilterOption, ...]
    | set[FilterOption]
    | None = None,
    fix_errors: bool = False,
    force: bool = False,
) -> bytes:
    """Optimize PNG bytes in memory."""
