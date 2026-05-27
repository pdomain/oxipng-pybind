"""Typing stub for the supported oxipng-pybind API."""

from collections.abc import Iterator, Sequence
from enum import Enum
from os import PathLike
from typing import overload

StrOrBytesPath = str | bytes | PathLike[str] | PathLike[bytes]
BytesLike = bytes | bytearray | memoryview
PaletteEntry = tuple[int, int, int] | tuple[int, int, int, int] | list[int]
Palette = Sequence[PaletteEntry]

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
        """Create a strip-chunk option for explicit PNG chunk names."""

    @staticmethod
    def keep(names: list[str] | tuple[str, ...] | set[str]) -> _CompatStripChunks:
        """Create a keep-chunk option for explicit PNG chunk names."""

class Deflater(Enum):
    libdeflater = "libdeflater"
    zopfli = "zopfli"

class Deflaters:
    @staticmethod
    def libdeflater(compression: int = 11) -> _CompatDeflater:
        """Create a libdeflater option with an explicit compression level."""

    @staticmethod
    def zopfli(iterations: int = 15) -> _CompatDeflater:
        """Create a zopfli option with an explicit iteration count."""

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

    @staticmethod
    def predefined(filters: Sequence[object] | Iterator[object]) -> _PredefinedFilters:
        """Create a predefined row-filter sequence."""

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

class _CompatColorType:
    kind: str
    bit_depth: int
    palette: tuple[tuple[int, ...], ...] | None
    transparent: int | tuple[int, int, int] | None

class _CompatStripChunks:
    mode: str
    names: tuple[str, ...]

class _CompatDeflater:
    kind: str
    value: int

class _PredefinedFilters:
    filters: tuple[str, ...]

_ScalarFilterOption = FilterStrategy | RowFilter | str
FilterOption = _ScalarFilterOption | _PredefinedFilters

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
        transparent: int | tuple[int, int, int] | Palette | None = None,
        *,
        bit_depth: BitDepth | int = BitDepth.eight,
    ) -> _CompatColorType:
        """Create a pyoxipng-compatible color descriptor; emits DeprecationWarning."""

class PngError(Exception):
    """Raised when oxipng cannot optimize the input PNG."""

class OptimizationResult:
    """PNG optimization sizes from a dry run."""

    @property
    def original_size(self) -> int: ...
    @property
    def optimized_size(self) -> int: ...

class RawImage:
    @overload
    def __init__(
        self,
        width: int,
        height: int,
        color_type: ColorType | str,
        bit_depth: BitDepth | int,
        data: BytesLike,
        *,
        palette: Palette | None = None,
        transparent: int | tuple[int, int, int] | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        data: BytesLike,
        width: int,
        height: int,
        *,
        color_type: _CompatColorType,
    ) -> None: ...
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
        | list[_ScalarFilterOption]
        | tuple[_ScalarFilterOption, ...]
        | None = None,
        fix_errors: bool = False,
        force: bool = False,
        optimize_alpha: bool | None = None,
        bit_depth_reduction: bool | None = None,
        color_type_reduction: bool | None = None,
        palette_reduction: bool | None = None,
        grayscale_reduction: bool | None = None,
        idat_recoding: bool | None = None,
        scale_16: bool | None = None,
        fast_evaluation: bool | None = None,
        timeout: float | None = None,
        max_decompressed_size: int | None = None,
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
    | list[_ScalarFilterOption]
    | tuple[_ScalarFilterOption, ...]
    | None = None,
    fix_errors: bool = False,
    force: bool = False,
    backup: bool = False,
    preserve_attrs: bool = False,
    optimize_alpha: bool | None = None,
    bit_depth_reduction: bool | None = None,
    color_type_reduction: bool | None = None,
    palette_reduction: bool | None = None,
    grayscale_reduction: bool | None = None,
    idat_recoding: bool | None = None,
    scale_16: bool | None = None,
    fast_evaluation: bool | None = None,
    timeout: float | None = None,
    max_decompressed_size: int | None = None,
) -> None:
    """Optimize a PNG file on disk."""

def analyze(
    input: StrOrBytesPath,
    *,
    level: int = 2,
    interlace: Interlacing | str | None = None,
    strip: StripChunks | _CompatStripChunks | str | None = None,
    deflate: Deflater | _CompatDeflater | str | None = None,
    filter: FilterOption
    | list[_ScalarFilterOption]
    | tuple[_ScalarFilterOption, ...]
    | None = None,
    fix_errors: bool = False,
    force: bool = False,
    optimize_alpha: bool | None = None,
    bit_depth_reduction: bool | None = None,
    color_type_reduction: bool | None = None,
    palette_reduction: bool | None = None,
    grayscale_reduction: bool | None = None,
    idat_recoding: bool | None = None,
    scale_16: bool | None = None,
    fast_evaluation: bool | None = None,
    timeout: float | None = None,
    max_decompressed_size: int | None = None,
) -> OptimizationResult:
    """Return PNG optimization sizes without writing output."""

def optimize_from_memory(
    data: BytesLike,
    *,
    level: int = 2,
    interlace: Interlacing | str | None = None,
    strip: StripChunks | _CompatStripChunks | str | None = None,
    deflate: Deflater | _CompatDeflater | str | None = None,
    filter: FilterOption
    | list[_ScalarFilterOption]
    | tuple[_ScalarFilterOption, ...]
    | None = None,
    fix_errors: bool = False,
    force: bool = False,
    optimize_alpha: bool | None = None,
    bit_depth_reduction: bool | None = None,
    color_type_reduction: bool | None = None,
    palette_reduction: bool | None = None,
    grayscale_reduction: bool | None = None,
    idat_recoding: bool | None = None,
    scale_16: bool | None = None,
    fast_evaluation: bool | None = None,
    timeout: float | None = None,
    max_decompressed_size: int | None = None,
) -> bytes:
    """Optimize PNG bytes in memory."""
